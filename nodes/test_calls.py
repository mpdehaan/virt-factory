#!/usr/bin/python


import xmlrpclib
import sys
import string

#url = "http://localhost:2112"
url = "http://172.16.56.109:2112"
server = xmlrpclib.ServerProxy(url)

print sys.argv
print server.test_add(100, 200)
str = string.join(sys.argv[1:])
print str
print server.sign_show(str)



