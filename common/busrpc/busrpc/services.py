import threading
import time
import traceback
import socket

import busrpc.qpid_transport
import busrpc.rpc
from busrpc.crypto import CertManager
from busrpc.misc import *

def _extract_names(full_class_name):
    parts = full_class_name.split(".")
    class_name = parts[len(parts) - 1]
    module_name = full_class_name.replace("." + class_name, "")
    return module_name, class_name

def _prepare_module_path(name):
    parts = name.split(".")
    parts.remove(parts[-1])
    return name, parts

def _create_instance(config, full_class_name):
    module_name, class_name = _extract_names(full_class_name)
    module_name, module_path = _prepare_module_path(module_name)
    module = __import__(module_name, globals(), None, module_path)
    instance_class = getattr(module, class_name)
    return instance_class(config)

class RPCDispatcher(object):

    def __init__(self, config, register_with_bridge = True, server_host = None, is_bridge_server=None):
        if is_bridge_server == None:
            self.is_bridge_server=not register_with_bridge
        else:
            self.is_bridge_server = is_bridge_server
        self.instances = {}
        self.hostname = socket.gethostname()
        if (server_host == None):
            self.server_host = config.server_host
        else:
            self.server_host = server_host
        self.name = config.server_name
        certdir = config.get_value('busrpc.crypto.certdir')
        pwd = config.get_value('busrpc.crypto.password')
        if not self.is_bridge_server:
            self.transport = busrpc.qpid_transport.QpidServerTransport(self.hostname + "!" + self.name, host=self.server_host)
        else:
            self.transport = busrpc.qpid_transport.QpidServerTransport(self.name, host=self.server_host)
        self.transport.callback = self.dispatch
        self.register_with_bridge = register_with_bridge
        self.runner_thread = None
        self.instance_method_cache = {}
        self.cert_mgr = CertManager(certdir, self.hostname)
        self.client_transport = self.transport.clone()
        if register_with_bridge:
            self.bridge = busrpc.rpc.lookup_service('bridge', self.client_transport, cert_mgr=self.cert_mgr)
        else:
            self.bridge = None
        for name in config.instances.iterkeys():
            instance = config.instances[name]
            self.add_instance(name, _create_instance(config, instance))

    def start(self):
        self.transport.start()
        while not self.transport.is_stopped:
            time.sleep(1)
        
    def stop(self):
        self.unregister_all()
        self.transport.stop()

    def register(self, namespace):
        if self.register_with_bridge:
            try:
                self.bridge.register_service(self.hostname, self.name, namespace)
                return True
            except Exception, e:
                print e
                traceback.print_exc()
                return False
        else:
            return True

    def unregister(self, namespace):
        if self.register_with_bridge:
            self.bridge.unregister_service(self.hostname, self.name, namespace)
        
    def unregister_all(self):
        for namespace in self.instances.keys():
            self.unregister(namespace)
        self.instances.clear()

    def dispatch(self, message):
        sender, hostname, namespace, called_method, encoded_params, was_encrypted = decode_rpc_request(message, cert_mgr=self.cert_mgr)
        print "Sender: %s, Host: %s, Namespace: %s, Method: %s, Encoded Params: %s" % (sender,
                                                                                       hostname,
                                                                                       namespace,
                                                                                       called_method,
                                                                                       encoded_params)
        if sender == None or namespace == None:
            return
        cache_key = ''.join([namespace, '.', called_method])
        method = None
        try:
            method = self.instance_method_cache[cache_key]
        except KeyError:
            try:
                print self.instances
                instance = self.instances[namespace]
                method = self._resolve_method(instance, called_method)
                self.instance_method_cache[cache_key] = method
            except KeyError, e:
                # no namespace match
                print e
                return None, None
        params = decode_object(encoded_params)
        results = method(*params)
        headers = {}
        if hasattr(method, '_header_generator'):
            method._header_generator(headers)
        return sender, encode_rpc_response(self.name, self.hostname, namespace, called_method,
                                           encode_object(results), headers=headers, cert_mgr=self.cert_mgr, encrypt=was_encrypted)

    def add_instance(self, namespace, instance):
        self.instances[namespace] = instance
        if not self.register(namespace):
            print "Error during registration!"
            self.instances.pop(namespace)

    def _resolve_method(self, instance, method_name):
        if method_name[0] == '_':
            return None
        else:
            try:
                attr = getattr(instance, method_name)
                if callable(attr):
                    return attr
                else:
                    return None
            except AttributeError:
                return None
