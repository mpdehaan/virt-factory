# Utility functions for dealing with libvirt, whether from
# the remote API or the polling scripts

"""
Virt-factory backend code.

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Adrian Likins <alikins@redhat.com>
Scott Seago <sseago@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import sys
import os
import subprocess
import libvirt
from nodes.codes import *

# db values, do not translate!
VIRT_STATE_NAME_MAP = {
   0 : "running",
   1 : "running",
   2 : "running",
   3 : "paused",
   4 : "shutdown",
   5 : "shutdown",
   6 : "crashed"
}


class VirtFactoryLibvirtConnection():

    def __init__(self):


        cmd = subprocess.Popen("uname -r", shell=True, stdout=subprocess.PIPE)
        output = cmd.communicate()[0]

        if output.find("xen") != -1:
            conn = libvirt.open(None)
        else:
            conn = libvirt.open("qemu:///system")

        if not conn:
           raise VirtException(comment="hypervisor connection failure")

        self.conn = conn

    def find_vm(self, mac_address=-1):
        """
        Extra bonus feature: mac_address = -1 returns a list of everything
        """
        conn = self.conn

        # name we use
        if mac_address != -1:
            needle = mac_address.replace(":","_").upper()

        vms = []

        # this block of code borrowed from virt-manager:
        # get working domain's name
        ids = conn.listDomainsID();
        for id in ids:
            vm = conn.lookupByID(id)
            vms.append(vm)
        # get defined domain
        names = conn.listDefinedDomains()
        for name in names:
            vm = conn.lookupByName(name)
            vms.append(vm)

        if mac_address == -1:
            return vms

        for vm in vms:
            if vm.name() == needle:
                return vm

        raise VirtException(comment="virtual machine %s not found" % needle)

    def shutdown(self, mac_address):
        return self.find_vm(mac_address).shutdown()

    def pause(self, mac_address):
        return suspend(self.conn,mac_address)

    def unpause(self, mac_address):
        return resume(self.conn,mac_address)

    def suspend(self, mac_address):
        return self.find_vm(mac_address).suspend()

    def resume(self, mac_address):
        return self.find_vm(mac_address).resume()

    def create(self, mac_address):
        return self.find_vm(mac_address).create()
    
    def destroy(self, mac_address):
        return self.find_vm(mac_address).destroy()

    def undefine(self, mac_address):
        return self.find_vm(mac_address).undefine()
   
    def get_status(self, mac_address):
        state = self.find_vm(mac_address).info()[1]
        return VIRT_STATE_NAME_MAP.get(state,"unknown")

