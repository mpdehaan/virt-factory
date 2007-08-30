#!/usr/bin/python

import command_class
import guest_cmds

import getopt
import os
import pprint

from rhpl.translate import _, N_, textdomain, utf8

from client import ampmlib

def register(mode_dict):
    mode_dict[Delete.mode_string] = Delete


class Delete(command_class.Command):
    mode_string = "delete"
    def print_help(self):
        print "\t --help, -h"
        print "\t --verbose, -v"
        print "\t --task_id <task_id>            delete a task from the task queue"
#        print "\t --profile <profile>            delete a profile"
        print "\t --user_id <user_id>            delete a user"
    
    def _parse_args(self, args):

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
                self.print_help()
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

            
        
