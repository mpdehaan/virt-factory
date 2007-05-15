import dbus

import busrpc.local.services as local_services
from busrpc.local.misc import *

class _LocalRPCMethod(object):

    def __init__(self, iface, namespace, method_name):
        self.iface = iface
        self.namespace = namespace
        self.method_name = method_name
        self.results = {}

    def __call__(self, *args):
        hashable_args = True
        try:
            return self.results[args]
        except TypeError:
            hashable_args = False
        except KeyError:
            params = encode_object(args)
            raw_results = self.iface.dispatch(self.namespace, self.method_name, params)
            results = decode_object(raw_results)
            if hashable_args and type(results).__name__ == "dict":
                try:
                    results["cache_return"]
                    self.results[args] =  results["call_results"]
                    return self.results[args]
                except KeyError:
                    return results
            else:
                return results

class LocalRPCProxy(object):

    def __init__(self, name, namespace, bus=None):
        try:
            self.service_name = name[name.index("!") + 1:]
        except ValueError:
            self.service_name = name
        self.namespace = namespace        
        if bus == None:
            self.bus = dbus.SystemBus()
        else:
            self.bus = bus
        self.methods = {}

    def __getattr__(self, name):
        retval = None
        try:
            retval = self.methods[name]
        except KeyError:
            retval = self._make_method(name)
            self.methods[name] = retval
        return retval

    def _make_method(self, name):
        iface = local_services.resolve_local_service(self.service_name, self.bus)
        return _LocalRPCMethod(iface, self.namespace, name)

def lookup_namespace(namespace, bus=None):
    bridge = local_services.resolve_local_service(local_services.Bridge.WELL_KNOWN_NAME)
    result = bridge.lookup_namespace(namespace)
    if result == "NONE":
        return None
    elif result[0:3] == "[L]":
        return LocalRPCProxy(result, namespace)
    # Disabling remote lookups for now
    #elif result[0:3] == "[R]":
    #    return RemoteRPCProxy(result)
    else:
        return None

