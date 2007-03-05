#!/usr/bin/python

import string
import sys
import traceback
import xmlrpclib


PASS="PASS"
FAIL="FAIL"


# base class for tests, may be something useful here later
class TestCase(object):
    def __init__(self, url=None):
        url = "http://localhost:5150"
        if url:
            self.url = url
        self.server = xmlrpclib.ServerProxy(self.url)
        self.results = {}
        self.verbose = 0

    def logFail(self, method, comment="", rc=None, exc=None, traceback=None):
        self.log(method, comment, FAIL, rc=rc, exc=exc, traceback=traceback)
        
    def logPass(self, method, comment="", rc=None, exc=None, traceback=None):
        self.log(method, comment, PASS, rc=rc, exc=exc, traceback=traceback)

    def log(self, method, comment="", status="UNDEF", rc=None, exc=None, traceback=None):
        name = "%s.%s" % (self.__class__.__name__, method)
        results = {'comment': comment, 'status':status }
        if exc:
            results["exc"] = exc
        if traceback:
            results["traceback"] = traceback
        if rc:
            results["returncode"] = rc
        self.results[name] = results

    def getToken(self, user="admin", password="fedora"):
        self.token = self.server.user_login(user, password)[1]['data']


    def run(self):
        for mh in self.cases:
            try:
                mh()
            except:
                info = sys.exc_info()
                self.logFail(mh.__name__, comment="Raised an uncaught exception", exc=info[0], traceback=info[2])

    def report(self):
        for result in self.results:
            info = self.results[result]
            print "method: %s status: %s comment: %s" % (result, info['status'], info['comment'] )
            if info.has_key("returncode") and info['status'] == "FAIL" or self.verbose > 1:
                print "Return code: %s" % info["returncode"]
            if info.has_key("exc"):
                print "Raised exception: %s" % info['exc']
            if info.has_key("traceback"):
                print "Traceback:\n%s" % string.join(traceback.format_list(traceback.extract_tb(info["traceback"])))
            print
            
                
     
