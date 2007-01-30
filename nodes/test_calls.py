#!/usr/bin/python


import xmlrpclib

server = xmlrpclib.ServerProxy("http://localhost:2112")


print server.test_add(100, 200)


