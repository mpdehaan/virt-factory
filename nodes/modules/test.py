#!/usr/bin/python


from codes import *
import web_svc



class Test(web_svc.WebSvc):
    def __init__(self):
        self.methods = {"test_add": self.add}
        web_svc.WebSvc.__init__(self)

    def add(self, numb1, numb2):
        return success((numb1 + numb2))


methods = Test()
register_rpc = methods.register_rpc