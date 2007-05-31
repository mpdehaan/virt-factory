import time
import sys

from busrpc.rpc import lookup_service
import busrpc.qpid_transport

transport = busrpc.qpid_transport.QpidTransport()
transport.connect()

fp = lookup_service("foo", transport, 'bogon.rdu.redhat.com')
bp = lookup_service("bar", fp.transport)
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
