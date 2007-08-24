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

if __name__ == "__main__":
   sys.path.append("../")

from nodes.codes import *
from nodes import virt_utils as virt_utils
from modules import web_svc


class Virt(web_svc.WebSvc):
    
    #=======================================================================
    
    def __init__(self):
 
        """
        Constructor.  Register methods and make them available.
        """
        
        # basic constructor stuff
        web_svc.WebSvc.__init__(self)
        self.logger.debug("finishing initialization of virt module...")
 
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
        
        self.logger.debug("acquiring connection to hypervisor")

    def get_conn(self):
	self.conn = virt_utils.VirtFactoryLibvirtConnection()
        return self.conn

# =====================================================================
   
    def install(self, target_name, system=True):

        """
        Install a new virt system by way of a named cobbler profile.
        """

        conn = self.get_conn()

        if conn is None:
            raise VirtException(comment="no connection")

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
   
    def shutdown(self, mac_address):
        """
        Make the machine with the given mac_address stop running.
        Whatever that takes.
        """
        self.get_conn()
        self.conn.shutdown(mac_address)
        return success()        

    #=======================================================================
   
    def pause(self, mac_address):

        """
        Pause the machine with the given mac_address.
        """
        self.get_conn()
        self.conn.suspend(mac_address)
        return success()

    #=======================================================================
   
    def unpause(self, mac_address):

        """
        Unpause the machine with the given mac_address.
        """

        self.get_conn()
        self.conn.resume(mac_address)
        return success()

    #=======================================================================

    def create(self, mac_address):

        """
        Start the machine via the given mac address. 
        """
        self.get_conn()
        self.conn.create(mac_address)
        return success()
 
    # ======================================================================

    def destroy(self, mac_address):

        """
        Pull the virtual power from the virtual domain, giving it virtually no
        time to virtually shut down.
        """
        self.get_conn()
        self.conn.destroy(mac_address)
        return success()


    #=======================================================================

    def undefine(self, mac_address):
        
        """
        Stop a domain, and then wipe it from the face of the earth.
        by deleting the disk image and it's configuration file.
        """

        self.get_conn()
        self.conn.undefine(mac_address)
        return success()

    #=======================================================================

    def get_status(self, mac_address):

        """
        Return a state suitable for server consumption.  Aka, codes.py values, not XM output.
        """
        
        self.get_conn()
        return success("STATE=%s" % self.conn.get_status(mac_address))


methods = Virt()
register_rpc = methods.register_rpc


