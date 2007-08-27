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
    command = Pause(args,api)


class Pause(command_class.Command):
    def print_help(self):
        print "ampm pause profile_name [--profile_id] <profile_id>"

    def _parse_args(self, args):
        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",
                                        "profile_id="])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
            # FIXME: error handling


        profiles = []
        profile_ids = []
        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                self.print_help()
                return
            if opt in ["-v", "--verbose"]:
                self.verbose = self.verbose + 1
            if opt in ["--profile_id"]:
                profile_ids.append(val)


        profiles = args
        print profiles
        for profile in profiles:
            (retcode, data) = self.api.profile_get_by_name(profile)
            pprint.pprint(data)
            if retcode > 0:
                self.show_error(retcode, data)
                continue
            if not data:
                continue
            profile_ids.append(data['data']['id'])

        print profile_ids

        for profile_id in profile_ids:
           (retcode, data) = self.api.deployment_pause(profile_id)
           if retcode > 0:
               self.show_error(retcode, data)
               continue

        
