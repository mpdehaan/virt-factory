import os
import simplejson
import threading

import busrpc.remote.transport as remote_transport

def parse_message(msg):
    parts = msg.split("\n\n")
    if len(parts) < 2:
        return None, None

    return simplejson.loads(parts[0]), parts[1]

class RPCService(object):

    def __init__(self, name, use_glib_loop=False):
        print "use_glib_loop: %s" % (use_glib_loop)
        self.name = name
        print "Establishing remote RPCService on name %s" % (name)
        self.instance = None
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
        self.transport.publish_queue(self.name, self._message_handler, use_glib_loop=use_glib_loop)

    def set_instance(self, instance):
        self.instance = instance

    def shutdown(self):
        self.transport.shutdown()

    def _message_handler(self, queue_name, transport, msg):
        try:
            headers, body = parse_message(msg)
            if headers == None:
                return
            
            reply_to = str(headers['reply_to'])
            method_name = headers['method_name']
            method = self._resolve_method(self.instance, method_name)
            try:
                if not method == None:
                    params = simplejson.loads(body)
                    result = method(*params)
                    encoded_result = simplejson.dumps(result)
                    transport.send(reply_to, encoded_result)
                else:
                    result = simplejson.dumps({"Error":"Method %s not found" % (method_name)})
                    transport.send(reply_to, result)
            except Exception, e:
                result = simplejson.dumps({"Error":str(e)})
                transport.send(reply_to, result)
        except Exception, e:
            print e
            
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
        
class DirectoryService(object):

    WELL_KNOWN_NAME = "com.redhat.busrpc.DirectoryService"

    def __init__(self):
        object.__init__(self)
        self.namespaces_to_hosts = {}
        self.hosts_to_namespaces = {}
        self.registration_lock = threading.RLock()
        

    def register_namespace(self, host_name, server, namespace):
        print "Registering %s %s %s" % (host_name, server, namespace)
        try:
            self.registration_lock.acquire()
            if not self.namespaces_to_hosts.has_key(namespace):
                self.namespaces_to_hosts[namespace] = []
            self.namespaces_to_hosts[namespace].append(host_name + ":" + server)
            if not self.hosts_to_namespaces.has_key(host_name + ":" + server):
                self.hosts_to_namespaces[host_name] = []
            self.hosts_to_namespaces[host_name].append(server + ":" + namespace)
        finally:
            self.registration_lock.release()


    def unregister_namespace(self, host_name, server, namespace):
        print "Unregistering %s %s %s" % (host_name, server, namespace)
        try:
            self.registration_lock.acquire()
            if self.namespaces_to_hosts.has_key(namespace):
                try:
                    self.namespaces_to_hosts[namespace].remove(host_name + "!" + server)
                except ValueError:
                    pass
                if len(self.namespaces_to_hosts[namespace]) == 0:
                    self.namespaces_to_hosts.pop(namespace)
            if self.hosts_to_namespaces.has_key(host_name):
                try:
                    self.hosts_to_namespaces[host_name].remove(server + "!" + namespace)
                except ValueError:
                    pass
                if len(self.hosts_to_namespaces[host_name]) == 0:
                    self.hosts_to_namespaces.pop(host_name)
        finally:
            self.registration_lock.release()

    def lookup_namespace(self, namespace):
        print "Looking up %s" % (namespace)
        retval = None
        try:
            self.registration_lock.acquire()
            if self.namespaces_to_hosts.has_key(namespace):
                print self.namespaces_to_hosts
                hosts = self.namespaces_to_hosts[namespace]
                if len(hosts) > 0:
                    if len(hosts) > 1:
                        # Round-robin namespace references
                        retval = hosts.pop(0)
                        hosts.append(retval)
                    else:
                        retval = hosts[0]
        finally:
            self.registration_lock.release()
        if not retval == None:
            parts = retval.split(":")
            retval = ''.join([parts[0], "!", "com.redhat.busrpc.Bridge", "!", parts[1], "!", namespace])
        print "Found %s" % (retval)
        return retval

if __name__ == "__main__":
    rpc = RPCService(DirectoryService.WELL_KNOWN_NAME)
    rpc.set_instance(DirectoryService())
    
