import simplejson
import binascii

import busrpc.rpc
import qpid_transport
from qpid_util import encrypt, decrypt

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

def decode_rpc_request(message, cert_mgr=None):
    headers, args = message.split('\n\n')
    if is_secure(headers):
        if not cert_mgr == None:
            name, value  = headers.split(':')
            headers, args = decrypt(value.strip(), args, cert_mgr)
        else:
            raise qpid_transport.QpidTransportException('CertManager not found for secure content')
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

def decode_rpc_response(message, cert_mgr=None):
    all_headers, results = message.split('\n\n')
    if is_secure(all_headers):
        if not cert_mgr == None:
            all_headers, results = decrypt(all_headers['secure-host'], results, cert_mgr)
        else:
            raise qpid_transport.QpidTransportException('CertManager not found for secure content')
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

def is_secure(raw_headers):
    return raw_headers.startswith('secure-host:')

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
