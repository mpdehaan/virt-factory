import socket

import busrpc.qpid_transport as qpid_transport
from busrpc.misc import *
from busrpc.logger import Logger

class _LocalRPCMethod(object):

    def __init__(self, transport, server, namespace, method_name, hostname, cert_mgr=None):
        self.transport = transport
        self.server = server
        self.namespace = namespace
        self.method_name = method_name
        self.hostname = hostname
        self.cert_mgr = cert_mgr
        self.results = {}
        self.params = {}
        self.logger = Logger()
##         self.partial_encoded_message = encode_partial_rpc_message(self.transport.queue_name,
##                                                                   self.namespace,
##                                                                   self.method_name,
##                                                                   self.hostname)

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
        encoded_call = encode_rpc_request(self.transport.queue_name,
                                          self.namespace,
                                          self.method_name,
                                          self.hostname,
                                          params,
                                          cert_mgr=self.cert_mgr)
        if not async_call:
            # need to retry (w/ short timeouts) to prevent startup race conditions
            raw_results = None
            if self.method_name == "register_service":
                raw_results = self.send_register_message(encoded_call)
            else:
                raw_results = self.transport.send_message_wait(self.server, encoded_call)
            sender, namespace, method, headers, results = decode_rpc_response(raw_results, cert_mgr=self.cert_mgr, logger=self.logger)
            if cache_return and headers.has_key('cache_results'):
                self.results[args] =  results
                results = self.results[args]
            return results
        else:
            self.transport.send_message(self.server, encoded_call)
            return None

    def send_register_message(self, encoded_call):
        tries = 10
        timeout = 5
        registered = False
        raw_results = None
        while registered == False:
            try:
                #print "Registering..."
                raw_results = self.transport.send_message_wait(self.server, encoded_call, timeout=timeout)
                registered = True
            except qpid_transport.QpidTransportException, e:
                tries = tries - 1
                if tries == 0:
                    raise e
        return raw_results

class RPCProxy(object):

    def __init__(self, name, service, transport, cert_mgr=None):
        attrs = self.__dict__
        attrs['server_name'] = name
        attrs['service'] = service
        attrs['transport'] = transport
        attrs['hostname'] = socket.gethostname()
        attrs['cert_mgr'] = cert_mgr

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
        method = _LocalRPCMethod(attrs['transport'], attrs['server_name'], attrs['service'], method_name,
                                 attrs['hostname'], cert_mgr=attrs['cert_mgr'])
        return method

def build_proxy(service_handle, transport, cert_mgr=None):
    hostname, server, service = service_handle.split('!')
    return RPCProxy(hostname + "!" + server, service, transport, cert_mgr=cert_mgr)

def lookup_service(name, transport, cert_mgr=None, host=None, server_name = None, use_bridge=False):
    if transport == None:
        transport = qpid_transport.QpidTransport()
        transport.connect()
    retval = None
    if use_bridge:
        bridge = busrpc.rpc.RPCProxy("busrpc.Bridge", "bridge", transport, cert_mgr=cert_mgr)
        if name == "bridge":
            return bridge
        service_handle = bridge.lookup_service(name, host)
    else:
        service_handle = get_handle(name, host, server_name)
        
    if not service_handle == None:
        retval = build_proxy(service_handle, transport, cert_mgr=cert_mgr)
    return retval
    
def get_handle(service, hostname, server):
    if not hostname == None and not server == None:
        return hostname + "!" + server + "!" + service
    else:
        return None
