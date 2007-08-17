#!/usr/bin/python

import getopt
import os
import pprint
import sys

from rhpl.translate import _, N_, textdomain, utf8

from client import ampmlib

def run(args):
    command = List(args)



class List(object):
    def __init__(self, args):
        self.api = ampmlib.Api(url="http://127.0.0.1:5150",
                               username="admin",
                               password="fedora")
        self.verbose = 0
        self.__parse_args(args)

    def print_help(self):
        print "valid modes are machines, deployments, status, profiles"

    def __parse_args(self, args):

        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
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

        if mode not in ["machines", "deployments", "status", "profiles"]:
            # raise error?
            print "incorrect mode"

        if mode == "machines":
            self.list_machines()

        if mode == "deployments":
            self.list_deployments()

        if mode == "status":
            self.list_status()

        if mode == "profiles":
            self.list_profiles()

    def list_machines(self):
        (retcode, data) = self.api.machine_list()
        if self.verbose > 2:
            pprint.pprint(data)
        for machine in data['data']:
            if machine['id'] == -1:
                continue
            print "hostname: %s id: %s profile_name: %s" % (machine['id'], machine['hostname'], machine['profile']['name'])

    def list_deployments(self):
        (retcode, data) = self.api.deployment_list()
        if self.verbose > 2:
            pprint.pprint(data)
        for deployment in data['data']:
            if deployment['id'] == -1:
                continue
            print "%s" % (deployment['display_name'])

    def list_status(self):
        (retcode, data) = self.api.deployment_list()
        if self.verbose > 2:
            pprint.pprint(data)
        for deployment in data['data']:
            if deployment['id'] == -1:
                continue
            print "%s:    %s" % (deployment['display_name'], deployment['state'])

    def list_profiles(self):
        (retcode, data) = self.api.profile_list()
        if self.verbose > 2:
            pprint.pprint(data)
        for profile in data['data']:
            if profile['id'] == -1:
                continue
            if self.verbose < 1:
                print "%s %s %s" % (profile['name'], profile['version'], profile['distribution']['name'])
            if self.verbose >= 1:
                print "%s %s %s %s %s %s" % (profile['name'], profile['version'],
                                             profile['distribution']['name'], profile['virt_storage_size'],
                                             profile['virt_ram'],  profile['valid_targets'])
#        pprint.pprint(data)

