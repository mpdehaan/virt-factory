import gobject 
import dbus
import dbus.service
import dbus.glib
import threading
import socket
import new
import os

import busrpc.guid
from busrpc.local.misc import *
from busrpc.local.bridge import Bridge
from busrpc.config import DeploymentConfig

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

class RPCDispatcher(dbus.service.Object):
    
    """Publishes services on the local dbus"""

    def __init__(self, config):
        self.dbus_methods = {"dispatch":("sss", "s")}
        self.instances = {}
        self.name = config.server_name
        self.path = name_to_path(self.name)
        self.bus_name = dbus.service.BusName(self.name,
                                             dbus.SystemBus())
        self._connect_dbus_methods()
        dbus.service.Object.__init__(self, self.bus_name, self.path)
        for name in config.instances.iterkeys():
            instance = _create_instance(config, config.instances[name])
            parts = name.split('.')
            self.add_instance(parts[len(parts) - 1], instance)

    def register(self, namespace):
        bridge = resolve_local_service(Bridge.WELL_KNOWN_NAME)
        return bridge.register_service(self.name, namespace)

    def unregister(self, namespace):
        bridge = resolve_local_service(Bridge.WELL_KNOWN_NAME)
        return bridge.unregister_service(self.name, namespace)

    def unregister_all(self):
        for namespace in self.instances.keys():
            self.unregister(namespace)
        self.instances.clear()

    def dispatch(self, namespace, called_method, encoded_params):
        instances = self.instances[namespace]
        instance = None
        if len(instances) > 1:
            instance = instances.pop()
            instances.insert(0, instance)
        else:
            instance = instances[0]
        method = self._resolve_method(instance, called_method)
        params = decode_object(encoded_params)
        results = method(*params)
        return encode_object(results)

    def add_instance(self, namespace, instance):
        if not self.instances.has_key(namespace):
            self.instances[namespace] = []
            self.instances[namespace].append(instance)
            if not self.register(namespace):
                print "Error during registration!"
                self.instances.pop(namespace)
        else:
            self.instances[namespace].append(instance)

    def _connect_dbus_methods(self):
        for method_name in self.dbus_methods.iterkeys():
            in_sig, out_sig = self.dbus_methods[method_name]
            m = self.__class__.__dict__[method_name]
            decorator = dbus.decorators.method(self.name, in_signature=in_sig, out_signature=out_sig)
            decorator(m)
            interface_table = self.__class__._dbus_class_table[self.__class__.__module__ + "." +
                                                               self.__class__.__name__]
            interface_table[self.name] = {method_name:m}

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

    def run(self):
        loop = gobject.MainLoop()
        try:
            loop.run()
        except:
            self.unregister_all()
