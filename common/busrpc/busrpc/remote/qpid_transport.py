import threading

import qpid.spec
import qpid.content
import qpid.client
import qpid.queue

from busrpc.remote.transport import Transport, ServerTransport
import busrpc.remote.qpid_util as qpid_util

class QpidTransport(Transport):

        def __init__(self, host='localhost', port=5672, user='guest',
                     password='guest', vhost='development'):
            self.credentials = {"LOGIN":user, "PASSWORD":password}
            self.channels = {}
            self.client = qpid.client.Client(host, port,
                                             qpid.spec.load("file:///etc/qpid/amqp.0-8.xml"),
                                             vhost=vhost)
            self.exchange_name = "busrpc"
            self.connected = False
            self.queue_name = None
            self.incoming_queue = None

        def connect(self):
            if self.connected:
                return
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
                                                             ack=False)
            self.connected = True

        def send_message(self, to, message):
            props={"content-type":"text/plain", "reply-to": self.queue_name}
            qpid_util.publish_message(self, exchange_name=self.exchange_name,
                                     routing_key_name=to, properties=props,
                                     message=message)

        def send_message_wait(self, to, message, timeout=60):
            self.send_message(to, message)
            try:
                msg = self.incoming_queue.get(timeout=timeout)
                return msg.content.body
            except qpid.queue.Empty:
                return None
           
        def channel(self, channel_id):
            try:
                return self.channels[channel_id]
            except KeyError:
                channel = self.client.channel(channel_id)
                channel.channel_open()
                self.channels[channel_id] = channel
                return channel

        def declare_queue(self):
            return qpid_util.declare_queue(self, auto_remove=True)

class QpidServerTransport(QpidTransport, ServerTransport):

    def __init__(self, service_name, host='localhost', port=5672, user='guest',
                 password='guest', vhost='development'):
        self.service_name = service_name
        self.callback = None
        self.max_workers = 2
        self.queue_name = None
        self.is_stopped = False
        QpidTransport.__init__(self, host, port, user, password, vhost)

    def start(self):
        if not self.connected:
            self.connect()
        for i in range(self.max_workers):
            threading.Thread(target=self._poll).start()

    def stop(self):
        self.is_stopped = True

    def declare_queue(self):
        return qpid_util.declare_queue(self, queue_name=self.service_name,
                                      create=True, auto_remove=True)        

    def _poll(self):
        while not self.is_stopped:
            try:
                msg = self.incoming_queue.get(timeout=1)
                self.callback(self, msg.content.body)
            except qpid.queue.Empty:
                pass

