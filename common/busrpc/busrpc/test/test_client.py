import time
import sys

from busrpc.local.rpc import lookup_namespace

fp = lookup_namespace("foo")
bp = lookup_namespace("bar")
if fp == None or bp == None:
    print "Lookup failed :("
    sys.exit(-1)    

bp.dict_test({'a':'A', 'b':'B'})

total_time = 0
iterations = 100

for i in range(0, iterations):
    start = time.time()
    fp.reverse("blah")
    bp.add(3, 10)
    fp.stupid_split("blahblahblah")
    total_time = total_time + time.time() - start

print "Avg time: %f" % ((total_time / 100))
