#!/usr/bin/python


import sys
import xmlrpclib
import time
import operator

server = xmlrpclib.ServerProxy("http://localhost:5150")

def gettoken():
    blip = server.user_login("admin", "fedora")
    return blip[1]['data']

def tokencheck(token):
    blip = server.token_check(token)
    

def average(seq):
        return reduce(operator.add,seq)/len(seq)


if __name__ == "__main__":
    
    count = int(sys.argv[1])
    print "count", count

    times = []
    i = 0
    timestart = time.time()
    while i < count:
        timelocal = time.time()
        token = gettoken()
#        tokencheck(token)
        timei = time.time() - timelocal
        times.append(timei)
        print i, timei
        i = i + 1

    avg_time = average(times)
    print "total time: %s" % (time.time() - timestart)
    print "average time: %s" % avg_time
    print "min time: %s" % min(times)
    print "max time: %s" % max(times)
    print "average rate: %s calls per second" % (1.0/avg_time)
