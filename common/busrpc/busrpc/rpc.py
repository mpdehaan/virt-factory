import busrpc.qpid_transport as qpid_transport
from busrpc.misc import *

class _LocalRPCMethod(object):

    def __init__(self, transport, server, namespace, method_name):
        self.transport = transport
        self.server = server
        self.namespace = namespace
        self.method_name = method_name
        self.results = {}
        self.params = {}
        self.partial_encoded_message = encode_partial_rpc_message(self.transport.queue_name,
                                                                  self.namespace,
                                                                  self.method_name)

    def __call__(self, *args, **kwargs):
        results = None
        is_async = kwargs.has_key('rpc_async')
        try:
            results = self.results[args]
        except TypeError:
            results =  self.make_call(args, False, async_call=is_async)
        except KeyError:
            results = self.make_call(args, True, async_call=is_async)
        return results

    def make_call(self, args, cache_encoded_args, cache_return=True, async_call=False):
        params = None
        if cache_encoded_args:
            try:
                params = self.params[args]
            except KeyError:
                params = encode_object(args)
                self.params[args] = params
        else:
            params = encode_object(args)
        encoded_call = self.partial_encoded_message + params
        if not async_call:
            raw_results = self.transport.send_message_wait(self.server, encoded_call)
            sender, namespace, method, headers, results = decode_rpc_response(raw_results)
            if cache_return and headers.has_key('cache_results'):
                self.results[args] =  results
                results = self.results[args]
            return results
        else:
            self.transport.send_message(self.server, encoded_call)
            return None
        

class RPCProxy(object):

    def __init__(self, name, service, transport):
        attrs = self.__dict__
        attrs['server_name'] = name
        attrs['service'] = service
        attrs['transport'] = transport

    def __getattr__(self, name):
        retval = None
        try:
            retval = self.__dict__[name]
        except KeyError:
            retval = self._make_method(name)
            self.__dict__[name] = retval
        return retval

    def _make_method(self, method_name):
        attrs = self.__dict__
        method = _LocalRPCMethod(attrs['transport'], attrs['server_name'], attrs['service'], method_name)
        return method

def build_proxy(service_handle, transport):
    hostname, server, service = service_handle.split('!')
    return RPCProxy(hostname + "!" + server, service, transport)

def lookup_service(name, transport, host=None):
    if transport == None:
        transport = qpid_transport.QpidTransport()
        transport.connect()
    bridge = busrpc.rpc.RPCProxy("busrpc.Bridge", "bridge", transport)
    retval = None
    if name == "bridge":
        retval = bridge
    else:
        service_handle = bridge.lookup_service(name, host)
        if not service_handle == None:
            retval = build_proxy(service_handle, transport)
    return retval
    