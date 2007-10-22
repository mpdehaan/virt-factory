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
    mode_dict[List.mode_string] = List
    


class List(command_class.Command):
    mode_string = "list"
    def print_help(self):
        print "\tList information about virt-factory"
        print "\tvalid sub modes are hosts, guests, status, profiles, tasks, users"
        print "\t\t hosts      list machines capabable of running guests"
        print "\t\t guests     list virtulized guests"
        print "\t\t status     list status of virtulized guests"
        print "\t\t profiles   list profiles available for creating guests or hosts"
        print "\t\t tasks      list tasks that are queued"
        print "\t\t users      list users"

    def _parse_args(self, args):

        try:
            opts, args = getopt.getopt(args, "hvm",
                                       ["help",
                                        "verbose",
                                        "machine="])
        except getopt.error, e:
            print _("Error parsing list arguments: %s") % e
            # FIXME: error handling

        machine = None
        for (opt, val) in opts:
            if opt in ["-h", "--help"]:
                self.print_help()
                return
            if opt in ["-v", "--verbose"]:
                self.verbose = self.verbose + 1
            if opt in ["--machine"]:
                machine = val

        if not args:
            self.print_help()
            return
        
        try:
            mode = args[0]
        except IndexError:
            raise
        

        if mode not in ["hosts", "guests", "status", "profiles", "tasks", "users"]:
            # raise error?
            print "incorrect mode"

        if mode == "hosts":
            self.list_hosts()

        if mode == "guests":
            self.list_guests()

        if mode == "status":
            self.list_status()

        if mode == "profiles":
            self.list_profiles()

        if mode == "tasks":
            self.list_tasks(machine)

        if mode == "users":
            self.list_users()

    def list_hosts(self):
        (retcode, data) = self.api.machine_list()
        if self.verbose > 2:
            pprint.pprint(data)
        for machine in data['data']:
            if machine['id'] == -1:
                continue
            print "hostname: %s id: %s profile_name: %s" % (machine.get('hostname','(pending)'), machine['id'],
                                                            machine['profile']['name'])

    def list_guests(self):
        (retcode, data) = self.api.deployment_list()
        if self.verbose > 2:
            pprint.pprint(data)
        for deployment in data['data']:
            if deployment['id'] == -1:
                continue
            print "%s %s %s on host %s" % (deployment.get('hostname', '(unknown)'),
                                           deployment['mac_address'],
                                           deployment['profile']['name'],
                                           deployment['machine'].get('hostname', '(unknown"'))

    def list_status(self):
        (retcode, data) = self.api.deployment_list()
        if self.verbose > 2:
            pprint.pprint(data)
        for deployment in data['data']:
            if deployment['id'] == -1:
                continue
            print "%s %s %s  on host %s is  %s" % (deployment.get('hostname', '(unknown)'),
                                                   deployment['mac_address'],
                                                   deployment['profile']['name'],
                                                   deployment['machine'].get('hostname', '(unknown"'),     
                                                   deployment['state'])

    def list_tasks(self, machine=None):
        where_args = {}
        if machine:
            # FIXME: look machine_id
            (retcode, data) = self.api.machine_get_by_hostname(machine)
            if self.verbose > 2:
                pprint.pprint(data)
            if data['data']:
                machine_id = data['data'][0]['id']
                where_args = {'machine_id': machine_id}
            else:
                where_args = {"machine_id": -1}
        
        (retcode, data) = self.api.task_list(where_args)
        if self.verbose > 2:
            pprint.pprint(data)

        for task in data['data']:
            print "%s %s %s %s %s %s" % (task['id'],
                                         task['action_type'],
                                         task['user']['username'],
                                         task['machine']['hostname'],
                                         task['state'],
                                         time.asctime(time.localtime(task['time'])))
                                   
        
        
    def list_users(self):
        (retcode, data) = self.api.user_list()
        if self.verbose > 2:
            pprint.pprint(data)

        for user in data['data']:
            if user['id'] == -1:
                continue

            print "%(id)s %(username)s %(email)s %(first)s %(last)s %(description)s" % user 


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

