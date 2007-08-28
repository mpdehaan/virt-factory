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
    command = Shutdown(args,api)


class Shutdown(command_class.Command):
    def print_help(self):
        print "ampm shutdown guest_name [--guest_id] <guest_id>"

    def _parse_args(self, args):
        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",
                                        "guest_id="])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
            # FIXME: error handling


        guest = []
        guests_ids = []
        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                self.print_help()
                return
            if opt in ["-v", "--verbose"]:
                self.verbose = self.verbose + 1
            if opt in ["--guests_id"]:
                guests_ids.append(val)


        guests = args
        for guest in guests:
            (retcode, data) = self.api.deployment_get_by_mac(guest)
            if retcode > 0:
                self.show_error(retcode, data)
                continue
            if not data:
                continue
            guests_ids.append(data['data'][0]['id'])


        for guest_id in guests_ids:
           (retcode, data) = self.api.deployment_shutdown(guest_id)
           if retcode > 0:
               self.show_error(retcode, data)
               continue

        
