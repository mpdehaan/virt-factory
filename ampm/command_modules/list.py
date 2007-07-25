#!/usr/bin/python

import getopt
import os
import sys

import ampmlib

def run(args):
    command = List(args)


class List(object):
    def __init__(self, args):
        self.api = ampmlib.Api(url="http://127.0.0.1:5150",
                               username="admin",
                               password="fedora")
        self.__parse_args(args)

    def __parse_args(self, args):

        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",
                                        "machines"])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e


        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                print_help()
            if opt in ["-m", "--machines", "machines"]:
                self.list_machines()

    def list_machines(self):
        self.api.machine_list()
    
