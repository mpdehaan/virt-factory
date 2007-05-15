import dbus
import simplejson

def name_to_path(name):
    path = name.replace(".", "/")
    return "".join(["/", path])

def resolve_local_service(service_name, bus=None):
    if bus == None:
        bus = dbus.SystemBus()
    svc = bus.get_object(service_name, name_to_path(service_name))
    return dbus.Interface(svc, dbus_interface = service_name)

def parse_message(message):
    parts = message.split("\n\n")
    if len(parts) == 0:
        return None
    else:
        return decode_object(parts[0]), parts[1]

class CustomEncoder(simplejson.JSONEncoder):
    def default(self, o):
        if hasattr(o, "json_encode"):
            return o.json_encode()
        else:
            return CustomEncoder.default(self, o)    

def decode_object(obj):
    return simplejson.loads(obj)

def encode_object(obj):
    return simplejson.dumps(obj, cls=CustomEncoder)

