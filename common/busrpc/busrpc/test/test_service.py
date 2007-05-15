import dbus

import busrpc.local.decorators
from busrpc.local.services import RPCDispatcher
from busrpc.config import DeploymentConfig

class Blang:

    def __init__(self, value):
        self.value = value

    def json_encode(self):
        import simplejson
        return simplejson.dumps(self.value)

class Foo:

    def __init__(self, config):
   	pass

    @busrpc.local.decorators.memoized
    def reverse(self, text):
        return text[::-1]

    def stupid_split(self, text):
        retval = {}
        string_val = []
        for c in text:
            string_val.append(c)
        retval["message"] = string_val
        return retval

class Bar:
   
    def __init__(self, config):
	pass 

    def add(self, first, second):
        return Blang(first + second)

    def dict_test(self, dict):
        print dict

if __name__ == "__main__":
    config = DeploymentConfig("../../configs/test.conf")
    dispatcher = RPCDispatcher(config)
    dispatcher.run()

    
