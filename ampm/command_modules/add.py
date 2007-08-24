#!/usr/bin/python

import command_class

import getopt
import os
import pprint
import sys
import time

from rhpl.translate import _, N_, textdomain, utf8

from client import ampmlib

def run(args, api):
    command = Add(args,api)


class Add(command_class.Command):

    def print_help(self):
        print "--username <username> --password <password> --first <first_name"
        print "     --middle <middle_name> --last <last_name> --email <email address>"
        print "     --description <desription>"

    def _parse_args(self, args):

        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",
                                        "user"])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
            self.print_help()
            # FIXME: error handling


        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                self.print_help()
                return
            if opt in ["-v", "--verbose"]:
                self.verbose = self.verbose + 1

        try:
            mode = args[0]
        except IndexError:
            raise

        if mode not in ["user"]:
            # raise error?
            print "incorrect mode"

        if mode == "user":
            self.add_user(args)


    def add_user(self, args):
        try:
            opts, args = getopt.getopt(args[1:], "hvu:p:f:m:l:d:e:",
                                       ["help",
                                        "verbose",
                                        "username=",
                                        "password=",
                                        "first=",
                                        "middle=",
                                        "last=",
                                        "description=",
                                        "email="])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
            # FIXME: error handling

        required_args = ["--username", "--password",
                        "--first", "--last",
                        "--description", "--email"]
        passed_args = []
        for (opt, val) in opts:
            passed_args.append(opt)

        missing_args = []
        for required_arg in required_args:
            if required_arg not in passed_args:
                missing_args.append(required_arg)

        if missing_args:
            for missing_arg in missing_args:
                print "%s is a required argument" % missing_arg
            return
        
        username = password = first = middle =  None
        last = description = email = None
        
        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                self.print_help()
                return
            if opt in ["-v", "--verbose"]:
                self.verbose = self.verbose + 1
            if opt in ["-u", "--username"]:
                username = val
            if opt in ["-p", "--password"]:
                password = val
            if opt in ["-f", "--first"]:
                first = val
            if opt in ["-m", "--middle"]:
                middle = val
            if opt in ["-l", "--last"]:
                last = val
            if opt in ["-d", "--description"]:
                description = val
            if opt in ["-e", "--email"]:
                email = val



        (retcode, data) = self.api.user_add(username, password,
                                            first, last,
                                            description, email,
                                            middle)

        if retcode > 0:
            self.show_error(retcode, data)

        if self.verbose > 2:
            pprint.pprint(data)

