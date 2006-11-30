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

def provisioning_sync(websvc, args):
     
     distributions = distribution.distribution_list(websvc,{})
     images        = image.image_list(websvc,{})
     machines      = machine.machine_list(websvc,{})

     # cobbler can't be run multiple times at once...
     lock = threading.Lock()
     lock.acquire()

     try:
         api = cobbler.api.BootAPI()
         # api.serialize()
     except:
         lock.release()
         raise UncaughtException(traceback.format_exc())

     lock.release()
     return success()

