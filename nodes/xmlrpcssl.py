#!/usr/bin/python -tt
"""
This is a set of helpers to establish secure connections for XML-RPC
using pre-shared .pem files.
"""
import os, sys
from M2Crypto import SSL
from M2Crypto.m2xmlrpclib import SSL_Transport, Server
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

class SimpleSSLXMLRPCServer(SSL.SSLServer, SimpleXMLRPCServer):
    """
    An extension of SimpleXMLRPCServer that allows SSL handling.
    """
    def __init__(self, ssl_context, address, handler=None, handle_error=None):
        if handler is None: 
            handler = SimpleXMLRPCRequestHandler
        if handle_error is None:
            #self.handle_error = self._quietErrorHandler
            self.handle_error = self.errorHandler
        SSL.SSLServer.__init__(self, address, handler, ssl_context) 
        self.funcs = {}
        self.logRequests = 0
        self.instance = None

    def errorHandler(self, *args):
        print args
     
    def _quietErrorHandler(self):
        "Discard any errors during SSL communications"
        return

    def _dispatch(self, method, params):
        print method
        print params

        try:
            rc = self.funcs[method](*params)
        except Exception, e:
            print e
            print "BBBBBBBBBBBBBBBBBBBBBBLLLLLL"
            raise
        return rc

    

def daemonize(pidfile=None):
    """
    Daemonize this process with the UNIX double-fork trick.
    Writes the new PID to the provided file name if not None.
    """
    pid = os.fork()
    if pid > 0: 
        sys.exit(0)
    os.setsid()
    os.umask(0)
    pid = os.fork()
    if pid > 0:
        if pidfile is not None:
            open(pidfile, "w").write(str(pid))
        sys.exit(0)

class Factory:
    """
    Base class for Client and Server
    """
    def __init__(self):
        self.protocol = 'sslv23'
        self.verify = SSL.verify_peer|SSL.verify_fail_if_no_peer_cert
        self.verify_depth = 10
        self.callback = self._quietCallback
                
    def _initContext(self, pemfile):
        """
        Helper method for m2crypto's SSL libraries.
        """
        ctx = SSL.Context(self.protocol)
        ctx.load_cert(pemfile)
        ctx.load_client_ca(pemfile)
        ctx.load_verify_info(pemfile)
   #     ctx.set_verify(self.verify, self.verify_depth)
        ctx.set_session_id_ctx('xmlrpcssl')
        ctx.set_info_callback(self.callback)
        return ctx
        
    def _quietCallback(self, *args):
        """
        This prevents XML-RPC from printing out stuff to stderr/stdout.
        """
        print args
        return

    def newRemoteServer(self, pemfile, uri):
        """
        Setup a new remote XMLRPC server connection and return the
        server object.
        """
        ctx = self._initContext( pemfile)
        rserver = Server(uri, SSL_Transport(ssl_context=ctx))
        return rserver

    def newLocalServer(self, cafile, pemfile, port, xmlrpcserver=SimpleSSLXMLRPCServer):
        """
        Start a new local server running on the specified port.
        """
        ctx = self._initContext(cafile, pemfile)
        address = ('grimlock.devel.redhat.com', port)
        server = xmlrpcserver(ctx, address)
        return server  

def test_usage(myself):
    "Print usage message and exit"
    sys.stderr.write('To start a test server, run: %s server pemfile.pem\n'
                     % myself)
    sys.stderr.write('To test a running test server: %s client pemfile.pem\n'
                     % myself)
    sys.exit(1)

def test_ping(ident):
    "Return pong to show we are alive"
    return {'pong': ident}

def test(args):
    """
    Small testing utility.
    """
    if not args or len(args) < 3:
        test_usage(args[0])
    which = args[1]
    pemfile = args[2]
    cafile = args[3]
    if not os.access(pemfile, os.R_OK):
        sys.stderr.write('%s does not exist or is not readable\n' % pemfile)
        test_usage(args[0])
    fac = Factory()
    if which == 'server':
        port = 2112
        server = fac.newLocalServer(pemfile, port)
        sys.stdout.write('Server running on grimlock:%s using %s\n' 
                         % (port, pemfile))
        server.logRequests = 5
        server.register_function(test_ping)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            sys.stdout.write('Server shutdown.\n')
    elif which == 'client':
#	uri = "https://localhost:8080"

        uri = 'https://grimlock.devel.redhat.com:2112'

        rserver = fac.newRemoteServer( pemfile, uri)
        sys.stdout.write('Testing server on %s using %s\n' % (uri, pemfile))
        try:
#            ret = rserver.test_ping("foo")
            ret = rserver.test_add(2,3)

        except Exception, exc:
            sys.stdout.write('Test failed: %s\n' % exc)
            sys.exit(1)
        print "THE RETURN is: %s " % ret
        if ret == {'pong': 'foo'}:
            sys.stdout.write('Test successful.\n')
        else:
            sys.stdout.write('Test failed!\n')
    else:
        sys.stderr.write('%s is not understood.\n' % which)
        test_usage(args[0])
    
    
if __name__ == '__main__':
    test(sys.argv)
