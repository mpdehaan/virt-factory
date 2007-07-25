#!/usr/bin/python

"""
Virt-factory backend code.

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>

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

if __name__ == "__main__":
   sys.path.append("../")

from nodes.codes import *
from modules import web_svc

#XM_BIN = "/usr/sbin/xm"

class Virt(web_svc.WebSvc):
    
    #=======================================================================
    
    def __init__(self):
 
        """
        Constructor.  Register methods and make them available.
        """
 
        # get the server 
        fd = open("/etc/sysconfig/virt-factory/server")
        self.server_name = fd.read().strip()
        self.server_name = self.server_name.replace("http://","")
        self.server_name = self.server_name.split(":")[0]
        fd.close()
        self.methods = {
            "virt_install"  : self.install,
            "virt_shutdown" : self.shutdown,
            "virt_destroy"  : self.destroy,
            "virt_start"    : self.create,
            "virt_pause"    : self.pause,
            "virt_unpause"  : self.unpause,
            "virt_delete"   : self.undefine,
            "virt_status"   : self.get_status,
        }

        self.xen_conn = libvirt.open(None)  # warning: Xen only!
        if not self.xen_conn:
           raise VirtException(comment="Xen connection failure")
 
        web_svc.WebSvc.__init__(self)

    #=======================================================================
   
    def install(self, target_name, system=True):

        """
        Install a new virt system by way of a named cobbler profile.
        """

        if not os.path.exists("/usr/bin/koan"):
            raise VirtException(comment="no /usr/bin/koan")
        target = "profile"
        if system:
            target = "system"
        # TODO: FUTURE: set --virt-path in cobbler or here
        koan_args = [
            "/usr/bin/koan",
            "--virt",
            "--virt-graphics",  # enable VNC
            "--%s=%s" % (target, target_name),
            "--server=%s" % self.server_name
        ]
        rc = subprocess.call(koan_args,shell=False)
        if rc == 0:
            return success(0)
        else:
            raise VirtException(comment="koan returned %d" % rc)
 
    #=======================================================================

    def find_vm(self, mac_address):

        # name we use
        needle = mac_address.replace(":","_").upper()

        ids = self.xen_conn.listDomainsID()
        for domain in ids:
            try:
                domain = self.xen_conn.lookupByID(domain)
            except libvirt.libvirtError, lve:
                raise virtException(comment="libvirt go boom: %s" % repr(lve))          
            if domain.name() == needle:
                return domain

        raise VirtException(comment="virtual machine %s not found" % needle)
    
    #=======================================================================
   
    def shutdown(self, mac_address):

        """
        Make the machine with the given mac_address stop running.
        Whatever that takes.
        """
        self.find_vm(mac_address).shutdown()
        return success()        

    #=======================================================================
   
    def pause(self, mac_address):

        """
        Pause the machine with the given mac_address.
        """
        self.find_vm(mac_address).suspend()
        return success()

    #=======================================================================
   
    def unpause(self, mac_address):

        """
        Unpause the machine with the given mac_address.
        """

        self.find_vm(mac_address).resume()
        return success()

    #=======================================================================

    def create(self, mac_address):

        """
        Start the machine via the given mac address. 
        """
        self.find_vm(mac_address).create()
        return success()
 
    # ======================================================================

    def destroy(self, mac_address):

        """
        Pull the virtual power from the virtual domain, giving it virtually no
        time to virtually shut down.
        """
        self.find_vm(mac_address).destroy()
        return success()


    #=======================================================================

    def undefine(self, mac_address):
        
        """
        Stop a domain, and then wipe it from the face of the earth.
        by deleting the disk image and it's configuration file.
        """

        self.find_vm(mac_address).undefine()
        return success()

    #=======================================================================

    def get_status(self, mac_address):

        """
        Return a state suitable for server consumption.  Aka, codes.py values, not XM output.
        """
        
        # info returns a tuple of things, not documented in the code
        #  MEMORY = [1]
        #  STATE  = [0]

        # FIXME: we're invoking this via vf_nodecomm so it's stdout based
        # and rather messy, hence the STATE=foo in the return to make things
        # parseable.  When we move to the message bus we should just return
        # the state directly.

        state = self.find_vm(mac_address).info()[1]
        return success("STATE=%s" % VIRT_STATE_NAME_MAP.get(state,"unknown"))


    #=======================================================================

#    #def __get_xm_state(self, mac_address):
#
#        """
#
#        Run xm to get the state portion out of the output.
#        This will be a width 5 string that may contain:
#        
#           p       -- paused
#           r       -- running
#           b       -- blocked  (basically running though)
#           "-----" -- no state (basically running though)
#        
#        if not found at all, the domain doesn't at all exist, or it's off.
#        since we'll know if virtfactory deleted it, assume off.  if needed,
#        we can later comb the Xen directories to see if a file is still around.
#
#        """  
#
#        cmd_mac = mac_address.replace(":","_").upper()
#        output = self.__run_xm("list", None, True)
#        lines = output.split("\n")
#        if len(lines) == 1:
#            print "state --> off"
#            return "off"
#        for line in lines[1:]:
#            try:
#                (name, id, mem, cpus, state, time) = line.split(None)
#                if name == cmd_mac:
#                    print "state --> %s" % state
#                    return state       
#            except:
#                pass
#        print "state --> off"      
#        return "off"
#
#    #=======================================================================


methods = Virt()
register_rpc = methods.register_rpc

if __name__ == "__main__":
    # development testing only
    virt = Virt()

    # start a virtual system
    TEST = "00:16:3E:05:29:26"
    
    virt.create(TEST)
    virt.shutdown(TEST)
    virt.create(TEST)
    virt.pause(TEST)
    virt.unpause(TEST)
    virt.shutdown(TEST)
    virt.create(TEST)
    virt.destroy(TEST)




