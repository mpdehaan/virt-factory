#!/usr/bin/python

import getopt
import os
import pprint

from rhpl.translate import _, N_, textdomain, utf8

from client import ampmlib

def run(args, api):
    command = Delete(args, api)


class Delete(object):
    def __init__(self, args, api=None):
        self.api = ampmlib.Api(url="http://127.0.0.1:5150",
                               username="admin",
                               password="fedora")
        if api:
            self.api = api
        self.verbose = 0
        self.__parse_args(args)

    
    def __parse_args(self, args):

        task_id = None
        profile = None
        user_id = None
        
        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",
                                        "task_id=",
                                        "profile=",
                                        "user_id="])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
            # FIXME: error handling


        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                print_help()
            if opt in ["-v", "--verbose"]:
                self.verbose = self.verbose + 1
            if opt in ["--task_id"]:
                task_id = val
            if opt in ["--profile"]:
                profile = val
            if opt in ["--user_id"]:
                user_id = val

        if task_id is not None:
            self.delete_task(task_id)

        if user_id is not None:
            self.delete_user(user_id)

    def delete_task(self, task_id=None):
        (retcode, data) = self.api.task_delete(task_id)
        if self.verbose > 2:
            pprint.pprint(data)

    def delete_user(self, user_id=None):
        (retcode, data) = self.api.user_delete(user_id)
        if self.verbose > 2:
            pprint.pprint(data)

            
        
