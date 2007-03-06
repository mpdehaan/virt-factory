#!/usr/bin/python

"""
ShadowManager backend code.

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>

Thanks to:
Peter Vetere <pvetere@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

from codes import *
import web_svc
import os
import subprocess

# map of Xen number codes to states that make sense
VIRT_STATE_NAME_MAP = [
   "running", "running", "running", "paused", "shutdown", "shutoff", "crashed"
]

# FIXME: this node needs a way to rerun registration to update info.
# the easiest way to do this seems to be to save servername and other params in /etc/sysconfig
# during registration
# and initiate from here via RPC call.  shouldn't be virt specific though!


class Virt(web_svc.WebSvc):
    
    #=======================================================================
    
    def __init__(self):
 
        """
        Constructor.  Register methods and make them available.
        """
 
        # get the server 
        fd = open("/etc/sysconfig/virtfactory/server")
        self.server_name = fd.read().strip()
        fd.close()
        self.methods = {
            "virt_install" : self.command_install,
            "virt_stop"    : self.command_stop,
            "virt_start"   : self.command_start,
            "virt_delete"  : self.command_delete
        }
        web_svc.WebSvc.__init__(self)

    #=======================================================================
   
    def command_install(self, target_name, system=True):

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
   
    def command_shutdown(self, mac_address):

         """
         Make the machine with the given mac_address stop running.
         Whatever that takes.
         """

         (filename, uuid) = self.find_virt(mac_address)
         state = self.get_state(uuid)
         if self == "crashed":
             destroy(uuid)
         elif state == "paused":
             self.resume(uuid)
             self.shutdown(uuid)
         else:
             self.call(uuid, "shutdown")
    
    #=======================================================================
   
    def command_suspend(self, mac_address):

        """
        Pause the machine with the given mac_address.
        """

        (filename, uuid) = self.find_virt(mac_address)
        state = self.get_state(uuid)
        if state == "running":
            self.call(uuid, "suspend")
        else:
            raise VirtException(comment="can't suspend what isn't running")

    #=======================================================================
   
    def command_resume(self, mac_address):

        """
        Unpause the machine with the given mac_address.
        """

        (filename, uuid) = self.find_virt(mac_address)
        state = self.get_state(uuid)
        if state == "paused":
            return self.call(uuid, "suspend")
        else:
            raise VirtException(comment="can't resume what isn't paused")

    #=======================================================================

    def command_start(self, mac_address):

        """
        Start the machine via the given mac address, whether that means, 
        """

        (filename, uuid) = self.find_virt(mac_address)
        state = self.get_state(uuid)
        if state == "paused":
            self.call(uuid, "resume")
        elif state == "shutoff" or state == "shutdown" or state == "crashed":
            fd = open(filename)
            xml = fd.read()
            fd.close()
            connection = libvirt.open()
            try:
                domain = connection.createLinux(xml, 0)
            except:
                raise VirtException(comment="failed to create %s" % uuid)     
            return success(0)   

    #=======================================================================

    def find_virt(self, mac):

        """
        For a given mac address, if possible, return a tuple containing it's uuid and the XML filename
        that describes it.
        """

        # FIXME: use real XML parser in case it's not neatly formatted by koan in the future.

        files = glob.glob("/var/lib/koan/virt/*").extend(glob.glob("/var/koan/virt/*"))
        found = None
        for fname in files:
            fd = open(fname)
            xml = fd.read()
            if xml.find(mac) != -1:
                lines = xml.split("\n")
                for line in lines:
                    if line.find("<uuid>") != -1:
                        uuid = line.replace("<uuid>","").replace("</uuid>","").strip()
                        fd.close()
                        return (fname, uuid)
            fd.close()
        raise VirtException(comment="no system with mac=%s" % mac)
  
    #=======================================================================

    def get_state(self,uuid):

        """
        Return the Xen state code, mapped into a state we understand.
        There is other info we care about in domain.info(), but not yet...
        """        

        (conn, domain) = self.connect(self,uuid)
        domain_info = domain.info()
        return VIRT_STATE_NAME_MAP[domain_info[0]]

    #=======================================================================

    def command_delete(self, mac_address):
        
        """
        Stop a domain, and then wipe it from the face of the earth
        by deleting the disk image and it's configuration file.
        """

        (filename, uuid) = self.find_virt(mac_address)
        state = self.get_state(uuid)
        basename = os.path.basename(filename)
        if (state == "running" or state == "crashed" or state == "paused"): 
             self.command_shutdown(mac_address)
        try: 
             os.unlink("/var/lib/xen/images/%s.disk" % basename)
        except Exception, e:
             raise VirtException(comment="failure during delete of (%s): %s" % (mac_address, str(e)))
        return success()    
    

    #=======================================================================

    def connect(self,uuid):

        """
        Establish a libvirt connection with the given UUID'd system and return (conn, domain)
        objects as a tuple.
        """

        conn = libvirt.open(None)
        domain = None
        try:
            domain = lookupByUUIDString(uuid)
        except libvirt.libvirtError, lve:
            raise VirtException(comment = "Domain (%s) not found: %s" % (uuid, str(lve)))
        return (conn, domain)

    #=======================================================================

    def call(uuid, routine_name, *args):
 
        """
        Helper function used to send most commands to libvirt.
        """

        (conn, domain) = self.connect(uuid)

        # Get a reference to the domain's control routine.
        ctrl_func = None
        try:
            ctrl_func = getattr(domain, routine_name)
        except AttributeError:
            raise VirtualizationException, "Unknown function: %s" % routine_name

        result = 0
        try:
            result = apply(ctrl_func, args)
        except TypeError, te:
            raise VirtException(comment="invalid arguments (%s) to (%s): %s" % (str(args), routine_name, str(te)))

        if result != 0:
            raise VirtException(comment="op failed: (%s) on (%s): %s" % (routine_name, uuid, str(result)))
        return result


methods = Virt()
register_rpc = methods.register_rpc
