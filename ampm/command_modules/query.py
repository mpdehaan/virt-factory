#!/usr/bin/python

import getopt
import os
import pprint
import sys

from rhpl.translate import _, N_, textdomain, utf8

from ampm import ampmlib

def run(args):
    command = Query(args)


class Query(object):
    def __init__(self, args):
        self.api = ampmlib.Api(url="http://127.0.0.1:5150",
                               username="admin",
                               password="fedora")
        self.verbose = 0
        self.__parse_args(args)

    def __parse_args(self, args):

        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",
                                        "container=",
                                        "profile="])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
            # FIXME: error handling


        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                print_help()
            if opt in ["-v", "--verbose"]:
                self.verbose = self.verbose + 1
            if opt in ["--container"]:
                self.query_container(deployment=val)
            if opt in ["--profile"]:
                self.query_profile(deployment=val)

#        try:
#            mode = args[0]
#        except IndexError:
#            raise


    def query_container(self, deployment=None):
        print "bloop"
        if deployment is None:
            # we could try to figure out the local deployment name and use
            # that here FIXME
            print "need a deployment name"
        (retcode, data) = self.api.deployment_get_by_mac_address(deployment=deployment)
        if self.verbose > 2:
            pprint.pprint(data)

        print data['data'][0]['machine']['hostname']


    def query_profile(self, deployment=None):
        # FIXME, refactor this so we're not duping so much stuff
        if deployment is None:
            # we could try to figure out the local deployment name and use
            # that here FIXME
            print "need a deployment name"
        (retcode, data) = self.api.deployment_get_by_mac_address(deployment=deployment)
        if self.verbose > 2:
            pprint.pprint(data)

        profile_id = data['data'][0]['profile_id']
        (retcode, data)  = self.api.profile_get(id=profile_id)
        print data['data']['name']
        
