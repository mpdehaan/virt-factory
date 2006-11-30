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
       new_item = api.new_distro()
       # new_item.set_name
       # new_item.set_kernel
       # new_item.set_initrd
       # new_item.set_kernel_options
       # new_item.set_arch
       # new_item.set_ksmeta
       api.distros().add(new_item)

class CobblerTranslatedProfile:
   def __init__(self,api,from_db):
       new_item = api.new_image()
       # new_item.set_name
       # new_item.set_distro
       # new_item.set_kickstart 
       # new_item.set_kernel_options
       # new_item.set_virt_name
       # new_item.set_virt_file_size
       # new_item.set_virt_ram
       # new_item.set_ksmeta
       api.profiles().add(new_item)

class CobblerTranslatedSystem:
   def __init__(self,api,from_db):
       new_item = api.new_system()
       # new_item.set_name
       # new_item.set_profile
       # new_item.set_kernel_options
       # new_item.set_ksmeta
       # new_item.set_pxe_paddress
       api.systems().add(new_item)

# FIXME: need another ShadowManager backend object that will need to sync with
# /var/lib/cobbler/settings

def provisioning_sync(websvc, args):

     return True # disable until later...     

     (rc0, distributions) = distribution.distribution_list(websvc,{})
     (rc1, images)        = image.image_list(websvc,{})
     (rc2, machines)      = machine.machine_list(websvc,{})

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

