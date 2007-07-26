#!/usr/bin/python


class BaseModule(object):
    def __init__(self):
	pass

    def register_rpc(self, handlers):
        for meth in self.methods:
            handlers[meth] = self.methods[meth]


 
