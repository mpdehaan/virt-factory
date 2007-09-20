import threading
import os

from busrpc.services import RPCDispatcher
from busrpc.config import DeploymentConfig
from busrpc.misc import *
from busrpc.logger import Logger

class Bridge(object):

    WELL_KNOWN_NAME = "busrpc.Bridge"
    
    def __init__(self, config):
        self.registration_lock = threading.RLock()
        self.services = {}
        self.services_by_host = {}
        self.logger = Logger()

    def register_service(self, hostname, server, service):
        try:
            try:
                self.registration_lock.acquire()
                if not self.services.has_key(service):
                    self.services[service] = []
                self.services[service].append((hostname, server))
                if not self.services_by_host.has_key(hostname):
                    self.services_by_host[hostname] = []
                self.services_by_host[hostname].append((server, service))
            finally:
                self.registration_lock.release()
        except Exception, e:
            self.logger.log_exc()
            return False
        else:
            return True

    def list_servers_for_service(self, service):
        retval = None
        try:
            self.registration_lock.acquire()
            if self.services.has_key(service):
                host_list = self.services[service]
                retval = [hostname + "!" + server + "!" + service
                          for hostname, server in host_list]
        finally:
            self.registration_lock.release()
        return retval

    def unregister_service(self, hostname, server, service):
        retval = True
        try:
            self.registration_lock.acquire()
            if self.services.has_key(service):
                host_list = self.services[service]
                host_list.remove((hostname, server))
                if len(host_list) == 0:
                    self.services.pop(service)
            if self.services_by_host.has_key(hostname):
                service_list = self.services_by_host[hostname]
                service_list.remove((server, service))
                if len(service_list) == 0:
                    self.services_by_host.pop(hostname)
        finally:
            self.registration_lock.release()
        return retval

    def lookup_service(self, service, host):
        try:
            self.registration_lock.acquire()
            return self._do_local_lookup(service, host=host)
        finally:
            self.registration_lock.release()

    def _do_local_lookup(self, service, host=None):
        hostname = None
        server = None
        if host == None:
            if self.services.has_key(service):
                host_list = self.services[service]
                # Do round-robin rotation if more than
                # one is registered
                if len(host_list) > 1:
                    hostname, server = host_list.pop()
                    host_list.insert(0, (hostname, server))
                else:
                    hostname, server = host_list[0]
        else:
            if self.services_by_host.has_key(host):
                service_list = self.services_by_host[host]
                for reg_server, reg_service in service_list:
                    if reg_service == service:
                        server = reg_server
                        hostname = host
                        break
        return get_handle(service, hostname, server)
                
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
