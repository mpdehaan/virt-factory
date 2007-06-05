from M2Crypto import RSA
import base64

import qpid.content
import qpid.queue

from busrpc.crypto import CertManager, CryptoException

def declare_exchange(caller, channel_id=1,exchange_name='',
                     create=False, auto_remove=False,
                     exchange_type='direct'):
    channel = caller.channel(channel_id)
    create = not create
    channel.exchange_declare(exchange=exchange_name, type=exchange_type,
                                 passive=create, auto_delete=auto_remove)

def declare_queue(caller, channel_id=1, queue_name='',
                  create=False, auto_remove=False,
                  exclusive_use=False):
    channel = caller.channel(channel_id)
    create = not create
    msg = channel.queue_declare(queue=queue_name, passive=create,
                                exclusive=exclusive_use, auto_delete=auto_remove)
    if not msg == None and len(msg.fields) > 0:
        return msg.fields[0]
    else:
        return None
        
def bind_queue(caller, channel_id=1, queue_name='',
               exchange_name='', routing_key_name=''):
    channel = caller.channel(channel_id)
    channel.queue_bind(queue=queue_name, exchange=exchange_name,
                       routing_key=routing_key_name)

def register_consumer(caller, channel_id=1, queue_name='', exclusive_use=False, ack=True):
    channel = caller.channel(channel_id)
    reply = channel.basic_consume(queue=queue_name, exclusive=exclusive_use,
                                  no_ack=not ack)
    return caller.client.queue(reply.consumer_tag)

def get_registered_queue(caller, queue_tag):
    return caller.client.queue(queue_tag)

def publish_message(caller, channel_id=1, exchange_name='',
                    routing_key_name='',message='', props={}):
    channel = caller.channel(channel_id)
    msg = qpid.content.Content(message, properties=props)
    channel.basic_publish(exchange=exchange_name, routing_key=routing_key_name,
                          content=msg)
        
def ack_message(caller, channel_id=1, message=None):
    channel = caller.channel(channel_id)
    channel.basic_ack(message.delivery_tag, True)

def decrypt(host, blob, cert_mgr):
    if cert_mgr == None:
        return blob
    key = None
    headers = None
    results = None
    try:
        key = cert_mgr.load_pub_key(host)
        if key == None:
            raise CryptoException('Missing public key for %s' % host)
        print 'decoded blob: %s' % (blob)
        msg = key.public_decrypt(blob, RSA.pkcs1_padding)
        print 'decrypted msg: %s' % (msg)
        headers, results = msg.split('\n\n')
    finally:
        if not key == None:
            cert_mgr.release_pub_key(host, key)
    return headers, results

def encrypt(host, msg, cert_mgr):
    if cert_mgr == None:
        return msg
    key = None
    msg = None
    try:
        key = cert_mgr.load_private_key()
        if key == None:
            raise CryptoException('Missing private key')
        blob = key.private_encrypt(str(msg), RSA.pkcs1_padding)
        return 'secure-host:' + host + '\n\n' + blob
    finally:
        if not key == None:
            cert_mgr.release_private_key(key)    
