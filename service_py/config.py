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

# code for loading a few backend service parameters from a config
# file, and _potentially_ used by a CLI for initial setup/install...

from codes import *
from errors import *
import baseobj
import traceback
import threading
import cobbler.api
import shadow
import yaml

def config_list(websvc=None,args=None):
   config_file = open("/var/lib/shadowmanager/settings")
   data = config_file.read()
   ds = yaml.load(data).next()
   return success(ds)

def register_rpc(handlers):
   handlers["config_list"] = config_list




