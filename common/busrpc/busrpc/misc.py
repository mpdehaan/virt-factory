import simplejson

import busrpc.rpc
import qpid_transport

def encode_partial_rpc_message(sender, namespace, method):    
    return ''.join(['from:', sender, '\n',
                    'ns:', namespace, '\n',
                    'method:', method, '\n\n'])

def encode_rpc_message(sender, namespace, method, args):
    return ''.join(['from:', sender, '\n',
                   'ns:', namespace, '\n',
                   'method:', method, '\n\n', args])

def encode_rpc_response(sender, namespace, called_method, results, headers=None):
    retval = ''.join(['from:', sender, '\n',
                      'ns:', namespace, '\n',
                      'method:', called_method, '\n'])
    if not headers == None:
        for key in headers.iterkeys():
            retval = retval + key + ':' + headers[key] + '\n'
        retval = retval + '\n'
    else:
        retval = retval + '\n'
    retval = retval + results
    return retval

def decode_rpc_message(message):
    headers, args = message.split('\n\n')
    sender = None
    namespace = None
    method = None
    parts = headers.split('\n')
    for i in range(len(parts)):
        line_parts = parts[i].split(':')
        if line_parts[0] == 'from':
            sender = line_parts[1].strip(' ')
        elif line_parts[0] == 'ns':
            namespace = line_parts[1].strip(' ')
        elif line_parts[0] == 'method':
            method = line_parts[1].strip(' ')
    if not (sender == None and namespace == None
            and method == None and args == None):
        return sender, namespace, method, args.strip(' ')
    else:
        return None, None, None, None

def decode_rpc_response(message):
    all_headers, results = message.split('\n\n')
    sender = None
    namespace = None
    method = None
    headers = {}
    parts = all_headers.split('\n')
    for i in range(len(parts)):
        line_parts = parts[i].split(':')
        name, value = (line_parts[0], line_parts[1])
        value = value.strip(' ')
        if name == 'from':
            sender = value
        elif name == 'ns':
            namespace = value
        elif name == 'method':
            method = value
        else:
            headers[name] = value
    return sender, namespace, method, headers, simplejson.loads(results)

def decode_object(obj):
    return simplejson.loads(obj)

def encode_object(obj):
    return simplejson.dumps(obj, cls=CustomEncoder)

class CustomEncoder(simplejson.JSONEncoder):
    
    def default(self, o):
        if hasattr(o, "json_encode"):
            return o.json_encode()
        else:
            return simplejson.JSONEncoder.default(self, o)    
