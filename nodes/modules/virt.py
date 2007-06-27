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

# NOTE: this module implements virt support via koan and xm commands.
# the xm commands /should/ be replaced with libvirt logic, though
# libvirt inactive domain management is not currently available in RHEL5.
# if it does become available, switch the xm commands over.

import glob
import sys
import os
import subprocess

if __name__ == "__main__":
   sys.path.append("../")

from nodes.codes import *
from modules import web_svc

XM_BIN = "/usr/sbin/xm"

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
        koan_args = [
            "/usr/bin/koan",
            "--virt",
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

         self.__xm_command("shutdown", mac_address, [ "r", "p", "b", "-----" ])

    #=======================================================================
   
    def pause(self, mac_address):

        """
        Pause the machine with the given mac_address.
        """

        return self.__xm_command("pause", mac_address, [ "r", "b", "-----" ])


    #=======================================================================
   
    def unpause(self, mac_address):

        """
        Unpause the machine with the given mac_address.
        """

        return self.__xm_command("unpause", mac_address, [ "p" ])

    #=======================================================================

    def create(self, mac_address):

        """
        Start the machine via the given mac address. 
        """
  
        return self.__xm_command("create", mac_address, None)
   
    # ======================================================================

    def destroy(self, mac_address):

        """
        Pull the virtual power from the virtual domain, giving it virtually no
        time to virtually shut down.
        """

        return self.__xm_command("destroy", mac_address, [ "p", "b", "-----", "r" ])


    #=======================================================================

    def undefine(self, mac_address):
        
        """
        Stop a domain, and then wipe it from the face of the earth.
        by deleting the disk image and it's configuration file.
        """

        # make sure the machine is off, no warning time given
        killcode = self.__xm_command("destroy", mac_address, None)
        # allow it to be deleted -- use virsh for this as XM can't do it (?)
        return subprocess.call(["/usr/bin/virsh","undefine",mac_address], shell=True)

    #=======================================================================

    def get_status(self, mac_address):

        """
        Return a state suitable for server consumption.  Aka, codes.py values, not XM output.
        """

        state = self.__get_xm_state(mac_address)
        if state == "off":
            return success("STATE=off")
        elif state.find("p") != -1:
            return success("STATE=paused")
        elif state.find("b") != -1 or state.find("-----") != -1 or state.find("r") != -1:
            return success("STATE=running")
        else: 
            return success("STATE=unknown")
        return success()

    #=======================================================================

    def __get_xm_state(self, mac_address):

        """

        Run xm to get the state portion out of the output.
        This will be a width 5 string that may contain:
        
           p       -- paused
           r       -- running
           b       -- blocked  (basically running though)
           "-----" -- no state (basically running though)
        
        if not found at all, the domain doesn't at all exist, or it's off.
        since we'll know if virtfactory deleted it, assume off.  if needed,
        we can later comb the Xen directories to see if a file is still around.

        """  

        cmd_mac = mac_address.replace(":","_").upper()
        output = self.__run_xm("list", None, True)
        lines = output.split("\n")
        if len(lines) == 1:
            print "state --> off"
            return "off"
        for line in lines[1:]:
            try:
                (name, id, mem, cpus, state, time) = line.split(None)
                if name == cmd_mac:
                    print "state --> %s" % state
                    return state       
            except:
                pass
        print "state --> off"      
        return "off"

    #=======================================================================

    def __xm_command(self, command, mac_address, valid_states):
        
        """
        Execute an xm command for a mac_address only if the xm state is one of valid_states.
        Otherwise, it's an error.
        """

        current_state = self.__get_xm_state(mac_address)
        if valid_states is not None:
            print "valid states:", valid_states
            for state in valid_states:
                if current_state.find(state) != -1:
                    return self.__run_xm(command, mac_address, False)
            comment = "invalid state %s for %s on %s" % (current_state, command, mac_address)
            print comment
            raise VirtException(comment=comment)
        else:
            rc = self.__run_xm(command, mac_address, False)
            if rc == 0:
                return success(rc)
            else:
                raise VirtException(comment="failed")

    #=======================================================================

    def __run_xm(self, command, mac_address, string_out):

         """
         Run a xm command named "command" against a domain named after a mac_address
         (only with :'s converted to _ and lowercased), returning either an integer
         or a string based on the boolean value of string_out.
         """       

         if mac_address is not None:
             cmd_mac = mac_address.replace(":","_").upper()
             xm_command = "%s %s %s" % (XM_BIN, command, cmd_mac)
         else:
             xm_command = "%s %s" % (XM_BIN, command)
         print xm_command
         if string_out:
             (cin, couterr) = os.popen4(xm_command)
             output = couterr.read()
             return output
         else:
             return os.system(xm_command)


methods = Virt()
register_rpc = methods.register_rpc

if __name__ == "__main__":
    # development testing only
    virt = Virt()

    # install a virtual system
    # print virt.install("Test1",False)

    # start a virtual system
    TEST = "00:16:3E:53:83:0B"
    
    virt.create(TEST)
    virt.shutdown(TEST)
    virt.create(TEST)
    virt.pause(TEST)
    virt.unpause(TEST)
    virt.shutdown(TEST)
    virt.create(TEST)
    virt.destroy(TEST)




