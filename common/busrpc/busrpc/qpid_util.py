from M2Crypto import RSA
import base64

import qpid.content
import qpid.queue

from busrpc.crypto import CertManager, CryptoException

def declare_exchange(caller, channel_id=1,exchange_name='',
                     create=False, auto_remove=False,
                     exchange_type='direct'):
    channel = caller.channel(channel_id)
    channel.exchange_declare(exchange=exchange_name, type=exchange_type,
                                 passive=not create, auto_delete=auto_remove)

def delete_exchange(caller, channel_id=1,exchange_name=''):
    channel = caller.channel(channel_id)
    channel.exchange_delete(exchange=exchange_name)

def declare_queue(caller, channel_id=1, queue_name='',
                  create=False, auto_remove=False,
                  exclusive_use=False):
    channel = caller.channel(channel_id)
    msg = channel.queue_declare(queue=queue_name, passive=not create,
                                exclusive=exclusive_use, auto_delete=auto_remove)
    return msg.queue
        
def bind_queue(caller, channel_id=1, queue_name='',
               exchange_name='', routing_key_name=''):
    channel = caller.channel(channel_id)
    channel.queue_bind(queue=queue_name, exchange=exchange_name,
                       routing_key=routing_key_name)

def delete_queue(caller, channel_id=1,queue_name=''):
    channel = caller.channel(channel_id)
    channel.queue_delete(queue=queue_name)

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
