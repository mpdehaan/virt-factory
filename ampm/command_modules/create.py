#!/usr/bin/python

import getopt
import os
import pprint
import sys

from rhpl.translate import _, N_, textdomain, utf8

from client import ampmlib

def run(args):
    command = Create(args)


class Create(object):
    def __init__(self, args):
        self.api = ampmlib.Api(url="http://127.0.0.1:5150",
                               username="admin",
                               password="fedora")
        self.verbose = 0
        self.__parse_args(args)

    def __parse_args(self, args):

        hostname = None
        profile = None
        name = None
        
        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",
                                        "host=",
                                        "profile="])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
            # FIXME: error handling


        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                print_help()
            if opt in ["-v", "--verbose"]:
                self.verbose = self.verbose + 1
            if opt in ["--host"]:
                hostname = val
            if opt in ["--profile"]:
                profile = val


        if hostname is not None and profile is not None:
            self.create_deployment(hostname, profile)

    def create_deployment(self, hostname=None, profile=None):
        # we need to look up the host, and the profiles
        (retcode, data) = self.api.machine_get_by_hostname(hostname)
        if self.verbose > 2:
            pprint.pprint(data)
        machine_id = data['data'][0]['id']

        (retcode, data) = self.api.profile_get_by_name(profile)
        if self.verbose > 2:
            pprint.pprint(data)
        profile_id = data['data']['id']

        (retcode, data) = self.api.deployment_add(machine_id, profile_id)
        

        # hmm, that return struct is a bit odd...
        deployment_id = data['data']

        (retcode, data) = self.api.deployment_get(deployment_id)
        if self.verbose > 2:
            pprint.pprint(data)
        deployment_mac = data['data']['mac_address']
        print "%s deployed on host: %s with profile: %s" % (deployment_mac, hostname, profile)
