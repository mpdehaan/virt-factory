"""
ShadowManager backend code.

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Scott Seago <sseago@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

# note:  this contains helper code for working with cobbler.  methods here
# should not be surfaced in the external API, but should be methods on 
# things like image and deployments, etc.

# further note:  this class assumes validation has _already_ been
# done by various layers in the DB.  It will map DB constants
# to cobbler values, but it will not account for things like
# an invalid entry for a kernel filename, for instance.  In the event
# of something like that, exceptions will not be caught and will
# result (ultimately) in tracebacks to the caller.  This is by design
# as we don't want to cover up the source of what's going on from
# cobbler land...  MORAL: put the data in the database right,
# don't expect cobbler to validate it or otherwise fix it.

from codes import *
from errors import *
import baseobj
import traceback
import threading
import distribution
import image
import machine
import cobbler.api
import shadow

class CobblerTranslatedItem:
   def add(self):
       pass

class CobblerTranslatedDistribution:
   def __init__(self,api,from_db):
       NOTYET = """
       new_item = api.new_distro()
       new_item.set_name(from_db["name"])
       new_item.set_kernel(from_db["kernel"])
       new_item.set_initrd(from_db["initrd"])
       if from_db.has_key("kernel_options"):
           new_item.set_kernel_options(from_db["kernel_options"])
       # FIXME: mapping...
       # new_item.set_arch
       if from_db.has_key("kickstart_metadata"):
           new_item.set_ksmeta(from_db["kickstart_metadata"])
       api.distros().add(new_item)
       """
       pass

class CobblerTranslatedProfile:
   def __init__(self,api,from_db):
       NOTYET = """
       if not from_db.has_key("distribution"):
           # this data element is being used for testing or 
           # otherwise doesn't have a distribution assigned,
           # therefore there is no way for cobbler to provision it.
           return
       new_item = api.new_image()
       new_item.set_name(from_db["name"])
       new_item.set_distro(from_db["distribution"])
       if from_db.has_key("kickstart"):
           new_item.set_kickstart(from_db["kickstart"])
       if from_db.has_key("kernel_options"):
           new_item.set_kernel_options(from_db["kernel_options"])
       new_item.set_virt_name(from_db["name"])
       new_item.set_virt_file_size(from_db["virt_file_size"])
       new_item.set_virt_ram(from_db["virt_ram"])
       if from_db.has_key("kickstart_metadata"):
           new_item.set_ksmeta(from_db["kickstart_metadata"])
       api.profiles().add(new_item)
       """
       pass

class CobblerTranslatedSystem:
   def __init__(self,api,deployments,from_db):

       NOTYET= """
       # cobbler systems must know their profile.
       # we get a profile by seeing if a deployment references
       # the system.  

       if found == -1:
          # no deployment found for this machine, which means
          # we have no idea how to provision it.  it should
          # at least have a APPLIANCE_CONTAINER or ORDINARY_MACHINE
          # deployment set up for it.

       new_item = api.new_system()
       new_item.set_name(from_db["mac_address"])
       # new_item.set_profile
       # new_item.set_kernel_options
       # new_item.set_ksmeta
       new_item.set_pxe_paddress(from_db["pxe_address"])
       api.systems().add(new_item)
       """
       pass


# FIXME: need another ShadowManager backend object that will need to sync with
# /var/lib/cobbler/settings

def provisioning_sync(websvc, args):

     return True # disable until later...     

     (rc0, distributions) = distribution.distribution_list(websvc,{})
     (rc1, images)        = image.image_list(websvc,{})
     (rc2, machines)      = machine.machine_list(websvc,{})
     (rc3, deployments)   = deployment.deployment_list(websvc, {})

     # cobbler can't be run multiple times at once...
     lock = threading.Lock()
     lock.acquire()

     try:
         api = cobbler.api.BootAPI()
         api.distros().clear()
         api.profiles().clear()
         api.systems().clear()
         # cobbler can/will could raise exceptions on failure at any point...
         # return code checking is not needed.
         for d in distributions:
             CobblerTranslatedDistribution(api,d).add()
         for i in images:
             CobblerTranslatedProfile(api,i).add()
         for p in machines:
             CobblerTranslatedSystem(api,p).add()
         api.serialize()
         api.sync()
     except:
         lock.release()
         raise UncaughtException(traceback.format_exc())
 

     lock.release()
     return success()

