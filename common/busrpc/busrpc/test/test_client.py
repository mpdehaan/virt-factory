import time
import sys

from busrpc.rpc import lookup_service
from busrpc.crypto import CertManager
import busrpc.qpid_transport


def do_test():
    transport = busrpc.qpid_transport.QpidTransport()
    transport.connect()

    cm = CertManager('/home/sseago/tmpcert', 'skagway')
    
    fp = lookup_service("foo", transport, host='skagway', cert_mgr=cm)
    bp = lookup_service("bar", fp.transport, cert_mgr=cm)
    if fp == None or bp == None:
        print "Lookup failed :("
        sys.exit(-1)    
        
    total_time = 0
    iterations = 100

    for i in range(0, iterations):
        start = time.time()
        fp.reverse("blah")
        end = time.time()
        total_time = total_time + (end - start)
        start = time.time()
        bp.add(3, 10)
        end = time.time()
        total_time = total_time + (end - start)
        start = time.time()    
        fp.stupid_split("blahblahblah")
        end = time.time()
        total_time = total_time + (end - start)

    print "Avg time: %f" % ((total_time / (iterations * 3)))
