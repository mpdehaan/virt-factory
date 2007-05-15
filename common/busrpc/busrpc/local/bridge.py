import gobject 
import dbus
import dbus.service
import dbus.glib
import threading
import socket
import os

import busrpc.guid
from busrpc.local.misc import *

class Bridge(dbus.service.Object):

    """ Serves as a directory for all services published on the local dbus """

    WELL_KNOWN_NAME = "com.redhat.busrpc.Bridge"
    WELL_KNOWN_PATH = name_to_path(WELL_KNOWN_NAME)

    def __init__(self):
        self.remote_rpc_service = None
        self.registration_lock = threading.RLock()
        self.services = {}
        self.host_name = socket.gethostname()
        self.remote_name = ''.join([self.host_name, "!", Bridge.WELL_KNOWN_NAME])
        self.bus_name = dbus.service.BusName(Bridge.WELL_KNOWN_NAME,
                                             dbus.SystemBus())
        self.directory_service = None
        dbus.service.Object.__init__(self, self.bus_name,
                                     Bridge.WELL_KNOWN_PATH)

    def run(self):
        loop = gobject.MainLoop()
        try:
            loop.run()
        except Exception, e:
            print e

    @dbus.decorators.method(WELL_KNOWN_NAME,
                         in_signature="ss", out_signature="b")
    def register_service(self, name, namespace):
        print "Registering %s, %s" % (name, namespace)
        try:
            try:
                self.registration_lock.acquire()
                key = self.host_name + "!" + name
                if not self.services.has_key(key):
                    self.services[key] = []
                self.services[key].append(namespace)
                #self.directory_service.register_namespace(self.host_name, name, namespace)
            finally:
                self.registration_lock.release()
        except Exception, e:
            print e
            return False
        else:
            return True

    @dbus.decorators.method(WELL_KNOWN_NAME,
                         in_signature="ss", out_signature="b")
    def unregister_service(self, name, namespace):
        print "Unregistering %s, %s" % (name, namespace)
        retval = True
        try:
            self.registration_lock.acquire()
            key = self.host_name + "!" + name
            if self.services.has_key(key):
                namespaces = self.services[key]
                try:
                    namespaces.remove(namespace)
                    if len(namespaces) == 0:
                        self.services.pop(key)                    
                    #self.directory_service.unregister_namespace(self.host_name, name, namespace)
                except ValueError:
                    retval = False
            else:
                retval = False
        finally:
            self.registration_lock.release()
        return retval

    @dbus.decorators.method(WELL_KNOWN_NAME,
                           in_signature="s", out_signature="s")
    def lookup_namespace(self, namespace):
        ns_addr = self.do_local_lookup(namespace)
        #if ns_addr == None:
        #    ns_addr = self.do_remote_lookup(namespace)
        if ns_addr == None:
            ns_addr = "NONE"
        return ns_addr

    def do_local_lookup(self, namespace):
        retval = None
        for server in self.services.keys():
            namespaces = self.services[server]
            try:
                namespaces.index(namespace)
                retval = server
                break
            except ValueError:
                continue
        if not retval == None:
            return "[L]%s" % (retval)
        else:
            return retval

    # Not used right now
    def bridge_namespace_call(self, namespace, method, args):
        server = self.do_local_lookup(namespace)
        if server == None:
            raise Exception("Namespace %s is not registered" % (namespace))
        proxy = LocalRPCServiceProxy(server, namespace)
        func = getattr(proxy, method)
        return func(*args)

    def _verify_registration(service_name):
        try:
            self.registration_lock.acquire()
            try:
                index(self.services, self.host_name + ":" + service_name)
                return True
            except ValueError:
                return False
        finally:
            self.registration_lock.release()

if __name__ == "__main__":
    b = Bridge()
    b.run()
