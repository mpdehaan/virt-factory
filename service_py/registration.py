#!/usr/bin/python

from codes import *
import baseobj
import traceback
import threading


class Register(baseobj.BaseObject):
    
    def validate(self, operation):
        pass


def register_add(websvc, image_args):
    """
    register a system. Connects an instances with a hostname and mac address
    """

    return success(1)


def register_rpc(handlers):
    handlers["register_add"] = register_add
