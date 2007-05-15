import simplejson
import os

import busrpc.remote.transport as remote_transport

class _BridgedRemoteRPCMethod(object):

    def __init__(self, service_name, method_name, local_service_name, transport):
        self.service_name = service_name
        self.method_name = method_name
        self.local_service_name = local_service_name
        self.transport = transport
        
    def __call__(self, *args):
        headers = {}
        queue_name = None
        queue = None
        try:
            queue_name, queue = self.transport.allocate_reply_queue()
            headers['reply_to'] = queue_name
            headers['method_name'] = 'bridge_namespace_call'
            wrapped_call_info = []
            wrapped_call_info.append(self.local_service_name)
            wrapped_call_info.append(self.method_name)
            wrapped_call_info.append(args)
            params = simplejson.dumps(wrapped_call_info)
            msg = ''.join([simplejson.dumps(headers), "\n\n", params])
            result = self.transport.send_and_wait(self.service_name, queue,
                                                  msg)
            retval = simplejson.loads(result.content.body)
            if type(retval).__name__ == 'dict':
                try:
                    err_msg = retval['Error']
                    raise Exception(err_msg)
                except KeyError:
                    return retval
            else:
                return retval
        finally:
            if not queue_name == None and not queue == None:
                self.transport.deallocate_reply_queue(queue_name, queue)

class _RemoteRPCMethod(object):

    def __init__(self, service_name, method_name, transport):
        self.service_name = service_name
        self.method_name = method_name
        self.transport = transport
        object.__init__(self)

    def __call__(self, *args):
        params = simplejson.dumps(args)
        headers = {}
        retval = None
        queue_name = None
        queue = None
        try:
            queue_name, queue = self.transport.allocate_reply_queue()
            headers['reply_to'] = queue_name
            headers['method_name'] = self.method_name
            msg = ''.join([simplejson.dumps(headers), "\n\n", params])
            result = self.transport.send_and_wait(self.service_name, queue,
                                                  msg)
            retval = simplejson.loads(result.content.body)
            if type(retval).__name__ == 'dict':
                try:
                    err_msg = retval['Error']
                    raise Exception(err_msg)
                except KeyError:
                    return retval
            else:
                return retval
        finally:
            if not queue_name == None and not queue == None:
                self.transport.deallocate_reply_queue(queue_name, queue)
            

class RemoteRPCProxy(object):

    def __init__(self, name, transport=None):
        parts = name.split("!")
        self.local_service_name = None
        self.service_name = None
        if len(parts) == 4:
            self.service_name = parts[0].replace("[R]", "") + "!" + parts[1]
            self.local_service_name = parts[3]
        else:
            self.service_name = name
            self.local_service_name = None
        self.own_transport = False
        self.transport = None
        self.transport_config = None
        if transport == None:
            self._start_transport()
        else:
            self.transport = transport

    def discard(self):
        if self.own_transport:
            self.transport.shutdown()

    def _start_transport(self):
        self.own_transport = True
        self.transport_config = remote_transport.TransportConfig()
        try:
            transport_config.host = os.environ["MQ_HOST"]
        except KeyError:
            pass
        try:
            transport_config.port = int(os.environ["MQ_PORT"])
        except KeyError:
            pass        
        self.transport = remote_transport.QpidTransport(self.transport_config)
        self.transport.connect()

    def __getattr__(self, name):
        if self.local_service_name == None:
            return _RemoteRPCMethod(self.service_name, name, self.transport)
        else:
            return _BridgedRemoteRPCMethod(self.service_name, name,
                                           self.local_service_name, self.transport)
