#!/usr/bin/python

from rhpl.translate import _, N_, textdomain, utf8

from client import ampmlib

class Command(object):
    def __init__(self, args, api):
        self.api = api
        self.verbose = 0
        self._parse_args(args)

    def _parse_args(self, args):
        raise NotImplementedError
    
    def show_error(self, retcode, data):
        print "An error has occurred:"
        if data.has_key("comment"):
            print data['comment']
        return None
