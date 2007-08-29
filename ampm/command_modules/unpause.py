#!/usr/bin/python


import command_class
import guest_cmds

import getopt
import os
import pprint
import sys
import time

from rhpl.translate import _, N_, textdomain, utf8

from client import ampmlib

def run(args, api):
    command = Unpause(args,api)


class Unpause(guest_cmds.GuestCommand):
    mode_string = "unpause"
    
    def _parse_args(self, args):
        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",
                                        "guest_id="])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
            self.print_help()
            # FIXME: error handling


        guest = []
        self.guests_ids = []
        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                self.print_help()
                return
            if opt in ["-v", "--verbose"]:
                self.verbose = self.verbose + 1
            if opt in ["--guests_id"]:
                self.guests_ids.append(val)


        self.guests = args
        if self.check_missing_args():
            return
        
        self.find_guest_ids()
        
        for guest_id in self.guests_ids:
           (retcode, data) = self.api.deployment_unpause(guest_id)
           if retcode > 0:
               self.show_error(retcode, data)
               continue

        
