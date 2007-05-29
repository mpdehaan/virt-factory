import threading
import os

from busrpc.services import RPCDispatcher
from busrpc.config import DeploymentConfig
from busrpc.misc import *

class Bridge(object):

    WELL_KNOWN_NAME = "busrpc.Bridge"
    
    def __init__(self, config):
        self.registration_lock = threading.RLock()
        self.services = {}

    def register_service(self, name, namespace):
        try:
            try:
                self.registration_lock.acquire()
                key =  name
                if not self.services.has_key(key):
                    self.services[key] = []
                self.services[key].append(namespace)
            finally:
                self.registration_lock.release()
        except Exception, e:
            print e
            return False
        else:
            return True

    def unregister_service(self, name, namespace):
        retval = True
        try:
            self.registration_lock.acquire()
            key = name
            if self.services.has_key(key):
                namespaces = self.services[key]
                try:
                    namespaces.remove(namespace)
                    if len(namespaces) == 0:
                        self.services.pop(key)                    
                except ValueError:
                    retval = False
            else:
                retval = False
        finally:
            self.registration_lock.release()
        return retval

    def lookup_namespace(self, namespace):
        return self.do_local_lookup(namespace)

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
        return retval

    def _verify_registration(service_name):
        try:
            self.registration_lock.acquire()
            try:
                index(self.services, service_name)
                return True
            except ValueError:
                return False
        finally:
            self.registration_lock.release()

def start_bridge(config_path):
    config = DeploymentConfig(config_path)
    dispatcher = RPCDispatcher(config, register_with_bridge=False)
    try:
        dispatcher.start()
    except KeyboardInterrupt:
        dispatcher.stop()
    print "Exiting..."
