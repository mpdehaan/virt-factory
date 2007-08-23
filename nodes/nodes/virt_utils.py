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



def get_conn(self):


    cmd = subprocess.Popen("uname -r", shell=True, stdout=subprocess.PIPE)
    output = cmd.communicate()[0]

    if output.find("xen") != -1:
        conn = libvirt.open(None)
    else:
        conn = libvirt.open("qemu:///system")

    if not self.conn:
        raise VirtException(comment="hypervisor connection failure")

    return conn



def find_vm(conn, mac_address):
    """
    Extra bonus feature: mac_address = -1 returns a list of everything
    """

    # name we use
    collector = []
    if mac_address != -1:
        needle = mac_address.replace(":","_").upper()

    ids = conn.listDomainsID()
    for domain in ids:
        try:
            domain = conn.lookupByID(domain)
        except libvirt.libvirtError, lve:
            raise virtException(comment="libvirt go boom: %s" % repr(lve))   
        if mac_address!= -1:
            if domain.name() == needle:
                return domain
        else:
            collector.append(domain)

    if mac_address == -1:
        return collector

    raise VirtException(comment="virtual machine %s not found" % needle)

def shutdown(conn, mac_address):
    return conn.find_vm(mac_address).shutdown()

def pause(conn, mac_address):
    return conn.find_vm(mac_address).suspend()

def unpause(conn, mac_address):
    return conn.find_vm(mac_address).resume()

def create(conn, mac_address):
    return conn.find_vm(mac_address).create()
    
def destroy(conn, mac_address):
    return conn.find_vm(mac_address).destroy()

def define(conn, mac_address):
    return conn.find_vm(mac_address).undefine()
   
def get_status(conn, mac_address):
    state = find_vm(conn, mac_address).info()[1]
    return VIRT_STATE_NAME_MAP.get(state,"unknown")

