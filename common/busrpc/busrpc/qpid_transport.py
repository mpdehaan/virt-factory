import os
import socket
import threading
import Queue
import time
from M2Crypto import RSA

import qpid.spec
import qpid.content
import qpid.client
import qpid.queue
import qpid.peer

from busrpc.transport import Transport, ServerTransport
from busrpc.crypto import CertManager
import busrpc.qpid_util as qpid_util
from busrpc.logger import Logger

class QpidTransportException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)       

class QpidTransport(Transport):

    def __init__(self, host='localhost', port=5672, user='guest',
                 password='guest', vhost='development'):
        self.logger = Logger()
        self.nethostname = socket.gethostname()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.vhost = vhost
        self.credentials = {"LOGIN":user, "PASSWORD":password}
        self.channels = {}
        self.client = qpid.client.Client(host, port,
                                         qpid.spec.load("file:///usr/share/amqp/amqp.0-9.xml", "file:///usr/share/amqp/amqp-errata.0-9.xml"),
                                         vhost=vhost)
        self.exchange_name = "busrpc"
        self.connected = False
        self.queue_name = None
        self.incoming_queue = None

    def clone(self):
        retval = QpidTransport(self.host, self.port, self.user,
                               self.password, self.vhost)
        retval.connect()
        return retval

    def connect(self):
        if self.connected:
            return
        tries = 10
        wait_time = 0.25
        while self.connected == False:
            try:
                self.client.start(self.credentials)
                self.queue_name = self.declare_queue()
                qpid_util.declare_exchange(self, exchange_name=self.exchange_name,
                                           create=True,
                                           exchange_type="topic",
                                           auto_remove=False)
                qpid_util.bind_queue(self, queue_name=self.queue_name,
                                     exchange_name=self.exchange_name,
                                     routing_key_name=self.queue_name)
                self.incoming_queue = qpid_util.register_consumer(self, queue_name=self.queue_name,
                                                                  ack=True)
                self.connected = True
            except qpid.peer.Closed, e:
                tries = tries - 1
                if tries == 0:
                    raise e
                else:
                    self.logger.info("connect: Trying again...")
                    time.sleep(wait_time)
                    wait_time = wait_time + 0.25
                    self.client = qpid.client.Client(self.host, self.port,
                                       qpid.spec.load("file:///usr/share/amqp/amqp.0-9.xml", "file:///usr/share/amqp/amqp-errata.0-9.xml"),
                                       vhost=self.vhost)                    

    def send_message(self, to, message):
        properties = {"Content-Type":"text/plain", "Reply-To": self.queue_name}
        qpid_util.publish_message(self, exchange_name=self.exchange_name,
                                  routing_key_name=to, message=message,
                                  props=properties)

    def send_message_wait(self, to, message, timeout=60):
        self.send_message(to, message)
        try:
            msg = self.incoming_queue.get(timeout=timeout)
            qpid_util.ack_message(self, message=msg)
            return msg.content.body
        except qpid.queue.Empty:
            raise QpidTransportException("Send to %s timed out after %d secs" % (to, timeout))

    def channel(self, channel_id):
		try:
			return self.channels[channel_id]
		except KeyError:
			channel = self.client.channel(channel_id)
			channel.channel_open()
			self.channels[channel_id] = channel
			return channel

    def declare_queue(self):
            return qpid_util.declare_queue(self, create=True, auto_remove=True)
        

class QpidServerTransport(QpidTransport, ServerTransport):

    def __init__(self, service_name, host='localhost', port=5672, user='guest',
                 password='guest', vhost='development', workers=2, certdir=None, cryptopassword=None):        
        self.service_name = service_name
        self.callback = None
        self.max_workers = workers
        self.is_stopped = False
        self.closing_lock = threading.RLock()
        self.poll_done = False
        self.write_done = False
        self.pending_calls = qpid.queue.Queue()
        self.pending_sends = qpid.queue.Queue()
        QpidTransport.__init__(self, host, port, user, password, vhost)

    def start(self):
        if not self.connected:
            self.connect()
        self.queue_name = self.service_name
        threading.Thread(target=self._poll).start()
        threading.Thread(target=self._write).start()
        for i in range(self.max_workers):
            t = threading.Thread(target=self._dispatch)
            t.setDaemon(True)
            t.start()

    def stop(self):
        self.is_stopped = True

    def shutdown_if_done(self):
        # delete queues
        # delete exchanges
        if (self.poll_done and self.write_done):
            qpid_util.delete_queue(self, queue_name=self.queue_name)
            #qpid_util.delete_exchange(self, exchange_name=self.exchange_name)

    def send_message(self, to, message):
        self.pending_sends.put((to, message))

    def declare_queue(self):
        return qpid_util.declare_queue(self, queue_name=self.service_name, create=True, auto_remove=True)

    def _write(self):
        while not self.is_stopped:
            try:
                to, message = self.pending_sends.get(timeout=15)
                QpidTransport.send_message(self, to, message)
            except qpid.queue.Empty:
                pass
        try:
            self.closing_lock.acquire()
            self.write_done = True
            self.shutdown_if_done()
        finally:
            self.closing_lock.release()

    def _dispatch(self):
        while not self.is_stopped:
            call_body = self.pending_calls.get()
            try:
                addr, reply = self.callback(call_body)
                if (addr != None and reply != None):
                    self.send_message(addr, reply)
            except TypeError, e:
                self.logger.log_exc()

    def _poll(self):
        while not self.is_stopped:
            if (self.connected):
                is_closed = self.channel(1).closed
                if (is_closed):
                    #print "reopening.."
                    try:
                        del self.channels[1]
                    except KeyError:
                        pass
                    self.connected = False
            if (not self.connected):
                try:
                    self.connect()
                except Exception, e:
                    #try to connect again next iteration
                    #print "trying again later ",e
                    pass
            try:
                msg = self.incoming_queue.get(timeout=15)
                qpid_util.ack_message(self, message=msg)                
                self.pending_calls.put(msg.content.body)
            except qpid.queue.Empty:
                pass

        try:
            self.closing_lock.acquire()
            self.poll_done = True
            self.shutdown_if_done()
        finally:
            self.closing_lock.release()
