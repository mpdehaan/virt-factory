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

class QpidTransportException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)       

class QpidTransport(Transport):

    def __init__(self, host='localhost', port=5672, user='guest',
                 password='guest', vhost='development', certdir=None, cryptopassword=None):
        self.nethostname = socket.gethostname()
        self.cert_mgr = None
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.vhost = vhost
        self.credentials = {"LOGIN":user, "PASSWORD":password}
        self.channels = {}
        self.client = qpid.client.Client(host, port,
                                         qpid.spec.load("file:///etc/qpid/amqp.0-8.xml"),
                                         vhost=vhost)
        self.exchange_name = "busrpc"
        self.connected = False
        self.queue_name = None
        self.incoming_queue = None
        self.certdir = certdir
        self.cryptopassword = cryptopassword
        if not self.certdir == None and not self.cryptopassword == None:
            self._setup_certs()

    def clone(self):
        retval = QpidTransport(self.host, self.port, self.user,
                               self.password, self.vhost, certdir=self.certdir, cryptopassword=self.cryptopassword)
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
                    print "Trying again..."
                    time.sleep(wait_time)
                    wait_time = wait_time + 0.25
                    self.client = qpid.client.Client(self.host, self.port,
                                       qpid.spec.load("file:///etc/qpid/amqp.0-8.xml"),
                                       vhost=self.vhost)                    

    def send_message(self, to, message):
        message = qpid_util.encrypt(self.nethostname, message, self.cert_mgr)
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

    def _setup_certs(self):
        self.cert_mgr = CertManager(self.certdir, self.nethostname, self.cryptopassword)
        

class QpidServerTransport(QpidTransport, ServerTransport):

    def __init__(self, service_name, host='localhost', port=5672, user='guest',
                 password='guest', vhost='development', workers=2, certdir=None, cryptopassword=None):        
        self.service_name = service_name
        self.callback = None
        self.max_workers = workers
        self.is_stopped = False
        self.pending_calls = qpid.queue.Queue()
        self.pending_sends = qpid.queue.Queue()
        QpidTransport.__init__(self, host, port, user, password, vhost, certdir=certdir,
                               cryptopassword=cryptopassword)

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

    def send_message(self, to, message):
        self.pending_sends.put((to, message))

    def declare_queue(self):
        return qpid_util.declare_queue(self, queue_name=self.service_name, create=True, auto_remove=True)

    def _write(self):
        while not self.is_stopped:
            try:
                to, message = self.pending_sends.get(timeout = 30)
                QpidTransport.send_message(self, to, message)
            except qpid.queue.Empty:
                pass

    def _dispatch(self):
        while not self.is_stopped:
            call_body = self.pending_calls.get()
            parts = call_body.split('\n\n')
            if len(parts) > 0:
                if parts[0].startswith('secure-host:'):
                    print 'Detecting secure message'
                    name, value = parts[0].split(':')
                    call_body = qpid_util.decrypt(value, parts[1], self.cert_mgr)
                    print 'Decrypted message: %s' % (call_body)
            addr, reply = self.callback(call_body)
            if addr == None or reply == None:
                return
            else:
                self.send_message(addr, reply)

    def _poll(self):
        while not self.is_stopped:
            try:
                msg = self.incoming_queue.get(timeout=30)
                qpid_util.ack_message(self, message=msg)                
                self.pending_calls.put(msg.content.body)
            except qpid.queue.Empty:
                pass

