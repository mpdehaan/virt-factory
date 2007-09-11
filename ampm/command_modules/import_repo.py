#!/usr/bin/python

import command_class

import getopt
import os
import pprint
import sys
import time

from rhpl.translate import _, N_, textdomain, utf8

from client import ampmlib

def register(mode_dict):
    mode_dict[ImportRepo.mode_string] = ImportRepo

class ImportRepo(command_class.Command):
    mode_string = "import_repo"
    def print_help(self):
        print "\t Import the configured repos to the vf_server database"
        print "\t\t--help"
        print "\t\t--verbose"
        
    def _parse_args(self, args):

        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose"])
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


        if len(args) == 0:
            self.import_repos()

    def import_repos(self, args={}):
        
        (retcode, data) = self.api.provisioning_init()

        if retcode > 0:
            self.show_error(retcode, data)

        if self.verbose > 2:
            pprint.pprint(data)
