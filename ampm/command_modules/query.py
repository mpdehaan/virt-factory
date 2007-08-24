#!/usr/bin/python

import command_class

import getopt
import os
import pprint
import sys

from rhpl.translate import _, N_, textdomain, utf8

from client import ampmlib

def run(args, api):
    command = Query(args, api)


class Query(command_class.Command):
    def _parse_args(self, args):

        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",
                                        "container=",
                                        "profile="])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
            # FIXME: error handling
            raise


        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                print_help()
            if opt in ["-v", "--verbose"]:
                self.verbose = self.verbose + 1
            if opt in ["--container"]:
                self.query_container(deployment=val)
            if opt in ["--profile"]:
                self.query_profile(profile_name=val)

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
        (retcode, data) = self.api.deployment_get_by_mac(deployment=deployment)
        if self.verbose > 2:
            pprint.pprint(data)

        print data['data'][0]['machine']['hostname']


    def query_profile(self, profile_name=None):
        # FIXME, refactor this so we're not duping so much stuff
        if profile_name is None:
            # we could try to figure out the local deployment name and use
            # that here FIXME
            print "need a deployment name"
        profile_id = None
        (retcode, data) = self.api.profile_list()
        for profile in data['data']:
            if profile['id'] == -1:
                continue
            if profile['name'] == profile_name:
                profile_id = profile['id']

        (retcode, data)  = self.api.profile_get(id=profile_id)
        ret_profile = data['data']
        print "%s %s %s %s %s %s %s" % (ret_profile['name'], ret_profile['version'],
                                        ret_profile['distribution']['name'], ret_profile['virt_storage_size'],
                                        ret_profile['virt_ram'],  ret_profile['valid_targets'],
                                        ret_profile['puppet_classes'])
        
