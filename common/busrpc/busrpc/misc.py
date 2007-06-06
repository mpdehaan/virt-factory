import simplejson
import binascii

import busrpc.rpc
import qpid_transport

def encode_partial_rpc_message(sender, namespace, method, hostname):    
    return ''.join(['from:', sender, '\n',
                    'host:', hostname, '\n'
                    'ns:', namespace, '\n',
                    'method:', method, '\n\n'])

def encode_rpc_response(sender, hostname, namespace, called_method, results, headers=None, cert_mgr=None):
    retval = encode_partial_rpc_message(sender, namespace, called_method, hostname)
    if not headers == None:
        for key in headers.iterkeys():
            retval = retval + key + ':' + headers[key] + '\n'
        retval = retval + '\n'
    else:
        retval = retval + '\n'
    print results
    retval = retval + results
    if not cert_mgr == None:
        retval = cert_mgr.encrypt_message(hostname, retval)
    return retval

def decode_rpc_request(message, cert_mgr=None):
    if not cert_mgr == None:
        msg = cert_mgr.decrypt_message(message)
        try:
            headers, args = msg.split('\n\n')
        except:
            headers, args = silly_split(msg)
    else:
        headers, args = message.split('\n\n')
        if is_secure(headers):
            raise qpid_transport.QpidTransportException('CertManager not found for secure content')
    sender = None
    namespace = None
    method = None
    hostname = None
    parts = headers.split('\n')
    for i in range(len(parts)):
        line_parts = parts[i].split(':')
        if line_parts[0] == 'from':
            sender = line_parts[1].strip(' ')
        elif line_parts[0] == 'ns':
            namespace = line_parts[1].strip(' ')
        elif line_parts[0] == 'method':
            method = line_parts[1].strip(' ')
        elif line_parts[0] == 'host':
            hostname = line_parts[1].strip(' ')
    if not (sender == None and namespace == None
            and method == None and args == None):
        return sender, hostname, namespace, method, args.strip(' ')
    else:
        return None, None, None, None

def decode_rpc_response(message, cert_mgr=None):
    if not cert_mgr == None:
        message = cert_mgr.decrypt_message(message)
        all_headers, results = message.split('\n\n')
    else:
        all_headers, results = message.split('\n\n')
        if is_secure(all_headers):
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

def silly_split(message):
    import cStringIO
    buffer = cStringIO.StringIO()
    print >> buffer, message
    print len(buffer.getvalue().strip())
    return buffer.getvalue().strip().split('\n\n')

def is_secure(raw_headers):
    return raw_headers.startswith('secure-host')

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
