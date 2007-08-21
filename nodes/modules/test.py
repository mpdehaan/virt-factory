#!/usr/bin/python


from nodes.codes import *
from modules import web_svc



class Test(web_svc.WebSvc):
    def __init__(self):
        self.methods = {
            "test_add": self.add,
            "test_blippy": self.blippy,
            "test_qpid": self.qpid
        }
        web_svc.WebSvc.__init__(self)

    def add(self, numb1, numb2):
        return success(int(numb1) + int(numb2))

    def blippy(self, foo):
        fh = open("/tmp/blippy","w+")
        fh.close()
        return success(foo)

    def qpid(self, puppet_node):
        self.init_qpid()
        info = self.server.puppet_node_info("UNSET", puppet_node)
        return success(info)

methods = Test()
register_rpc = methods.register_rpc
