import command_class

import getopt
import os
import pprint
import sys
import time

from rhpl.translate import _, N_, textdomain, utf8

from client import ampmlib


class GuestCommand(command_class.Command):
    def print_help(self):
        if self.blurb:
            print "\t%s" % self.blurb
        print "\tampm %s guest_name [--guest_id] <guest_id>" % self.mode_string

    def check_missing_args(self):
        if self.guests == [] and self.guests_ids == []:
            self.print_help()
            return True
        return False

    def find_guest_ids(self):
        
        
        for guest in self.guests:
            if guest.find('.') > -1:
                (retcode, data) = self.api.deployment_get_by_hostname(guest)
            elif guest.find(':') > -1:
                (retcode, data) = self.api.deployment_get_by_mac(guest)
            else:
                print "%s does not look like a hostname or mac address" % guest
                
            if retcode > 0:
                self.show_error(retcode, data)
                continue
            if not data or data['data'] == []:
                continue
            self.guests_ids.append(data['data'][0]['id'])
