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
    command = Pause(args,api)


def register(modes_dict):
    modes_dict[Pause.mode_string] = Pause

class Pause(guest_cmds.GuestCommand):
    mode_string = "pause"
    blurb = "Pause a guest"
        
    def _parse_args(self, args):
        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",
                                        "guest_id="])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
            # FIXME: error handling

        self.guests_ids = []
        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                self.print_help()
                return
            if opt in ["-v", "--verbose"]:
                self.verbose = self.verbose + 1
            if opt in ["--guest_id"]:
                self.guests_ids.append(val)


        self.guests = args
        if self.check_missing_args():
            return
        
        self.find_guest_ids()

        for guest_id in self.guests_ids:
           (retcode, data) = self.api.deployment_pause(guest_id)
           if retcode > 0:
               self.show_error(retcode, data)
               continue

        
