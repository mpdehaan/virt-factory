import threading
import Queue
import time
import os
import gobject
import qpid.client
import qpid.queue
import qpid.spec
from qpid.content import Content
from qpid.message import Message
import busrpc.guid

class TransportConfig:
    """
    Simple config object
    """
    def __init__(self):
        self.host = "localhost"
        self.vhost = "test"
        self.port = 5672
        self.user = "guest"
        self.password = "guest"
        self.protocol_spec = "/etc/qpid/amqp.0-8.xml"

class QpidTransport(object):

    def __init__(self, config):
        self.transport_config = config
        self.qpid_exchange = "rh-busrpc"
        self.guid = guid.generate()
        self.lock = threading.RLock()
        self.allocation_lock = threading.RLock()
        self.msg_id = 0
        self.dispatchers = []
        self.idle_reply_queues = []
        self.all_queues = []

    def connect(self):
        self.qpid_client = qpid.client.Client(self.config().host, self.config().port,
                                         qpid.spec.load(self.config().protocol_spec))
        self.qpid_client.vhost = self.config().vhost
        self.client().start({"LOGIN": self.config().user, "PASSWORD": self.config().password})        
        self.qpid_channel = self.client().channel(1)
        self.channel().channel_open("test")
        self.channel().exchange_declare(0, self.qpid_exchange, "direct")

    def publish_queue(self, queue_name, message_handler, use_glib_loop=False):
        queue = self.setup_queue(queue_name)
        self.dispatchers.append(MessageDispatcher(queue_name, queue, self,
                                                  message_handler, use_glib_loop=use_glib_loop, auto_start=True))

    def send(self, queue_name, message):
        self.channel().basic_publish(exchange=self.qpid_exchange,
                                     routing_key=queue_name,
                                     content=Content(message))

    def send_and_wait(self, queue_name, reply_queue, message, timeout=120):
        self.send(queue_name, message)
        reply = None
        try:
            reply = reply_queue.get(True, timeout)
        except qpid.queue.Empty:
            reply = None
        return reply
                
        
    def shutdown(self, reason=None):
        for dispatcher in self.dispatchers:
            dispatcher.stop()
            time.sleep(5)
        self.dispatchers = None
        for name in self.all_queues:
            try:
                self.channel().basic_cancel(name)
                self.channel().queue_delete(queue=name)
            except:
                pass
        self.channel().close(reason)
        self.qpid_channel = None
        self.qpid_client = None
        
    def next_msgid(self):
        try:
            self.lock.acquire()
            self.msg_id = self.msg_id + 1
            return self.msg_id
        finally:
            self.lock.release()
            
    def setup_queue(self, queue_name):
        self.channel().queue_declare(queue=queue_name)
        self.channel().queue_bind(queue=queue_name, exchange=self.qpid_exchange,
                                  routing_key=queue_name)
        reply = self.channel().basic_consume(queue=queue_name, no_ack=True)
        queue = self.client().queue(reply.consumer_tag)
        try:
            self.lock.acquire()
            self.all_queues.append(reply.consumer_tag)
        finally:
            self.lock.release()
        return queue

    def allocate_reply_queue(self):
        retval = None
        queue_name = None
        queue = None
        try:
            self.allocation_lock.acquire()
            if len(self.idle_reply_queues) == 0:
                queue_name = guid.generate()
                queue = self.setup_queue(queue_name)
            else:
                queue_name, queue = self.idle_reply_queues.pop()
        finally:
            self.allocation_lock.release()
        return queue_name, queue

    def deallocate_reply_queue(self, queue_name, queue):
        try:
            self.allocation_lock.acquire()
            self.idle_reply_queues.append((queue_name, queue))
        finally:
            self.allocation_lock.release()

    def channel(self):
        return self.qpid_channel

    def client(self):
        return self.qpid_client

    def config(self):
        return self.transport_config

class MessageDispatcher:

    def __init__(self, queue_name, queue, transport, callback,
                 use_glib_loop=False, worker_count=1, auto_start=False):
        self.queue_name = queue_name
        self.qpid_queue = queue
        self.work_queue = Queue.Queue()
        self.workers = []
        self.worker_count = worker_count
        self.callback = callback
        self.transport = transport
        self.is_stopped = False
        self.use_glib_loop = use_glib_loop
        self.has_scheduled_dispatch = False
        if auto_start == True:
            self.start()
        
    def start(self):
        if self.use_glib_loop:
            print "Using glib main loop"
            gobject.timeout_add(100, self.poll_qpid_glib)
        else:
            print "Using threads"
            for i in range(self.worker_count):
                t = threading.Thread(target=self.poll_work)
                t.setDaemon(False)
                self.workers.append(t)
                t.start()            
                qpid_thread = threading.Thread(target=self.poll_qpid)
                self.workers.append(qpid_thread)
                qpid_thread.start()
        return self

    def stop(self):
        self.is_stopped =  True

    def poll_qpid(self):
        while not self.is_stopped:
            item = None
            try:
                item = self.qpid_queue.get(True, .05)
            except Queue.Empty:
                item = None
            if not item == None:
                self.work_queue.put(item)

    def poll_qpid_glib(self):
        item = None
        try:
            item = self.qpid_queue.get(True, .05)
        except Queue.Empty:
            item = None
        if not item == None:
            self.work_queue.put(item)
            if not self.has_scheduled_dispatch:
                gobject.timeout_add(100, self._glib_dispatch)
                self.has_scheduled_dispatch = True
        return not self.is_stopped

    def _glib_dispatch(self):
        while True:
            try:
                item = self.work_queue.get(True, .05)
                self._dispatch_message(self.queue_name, self.transport, item.content.body)
            except Queue.Empty:
                break
        self.has_scheduled_dispatch = False
        return False
            

    def poll_work(self):
        while not self.is_stopped:
            try:
                item = self.work_queue.get(True, .05)
                self._dispatch_message(self.queue_name, self.transport, item.content.body)
            except Queue.Empty:
                pass
    
    def _dispatch_message(self, queue_name, transport, body):
        self.callback(queue_name, transport, body)
        if self.use_glib_loop:
            return False
        
