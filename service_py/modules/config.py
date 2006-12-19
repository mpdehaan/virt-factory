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

import os
import yaml

from codes import *

CONFIG_FILE = "/var/lib/shadowmanager/settings"

# note: if the user rsync's too close the arch info won't be in the path,
# and this means we can't fill in the arch.  so the defaults probably
# slurp a bit too much default info but at least it's not pulling in
# all the FC's.

defaults = {
    "this_server" : {
       "address" : "127.0.0.1"
    }, 
    "databases" : {
       "primary" : "/var/lib/shadowmanager/primary_db"
    },
    "logs" : {
       "service" : "/var/lib/shadowmanager/svclog"
    },
    "mirrors" : {
       "FC-6"   : "rsync://rsync.devel.redhat.com/engarchive/released/FC-6/GOLD"
    }
}

def config_list(websvc=None,config_args=None):

   if not os.path.exists(CONFIG_FILE):
       raise MisconfiguredException(comment=CONFIG_FILE)

   config_file = open(CONFIG_FILE)
   data = config_file.read()
   ds = yaml.load(data).next()

   return success(ds)

def config_reset(websvc=None,config_args=None):
   
   config_file = open(CONFIG_FILE,"w+")
   data = yaml.dump(defaults)
   config_file.write(data)

   print """
   The configuration values in %s have been reset.

   Next steps:
      (1) Edit the address field and mirror list in %s
          Change other settings as desired.
      (2) Run 'shadow import' to import distributions from your selected mirrors.
      (3) Test the configuration by logging in using the Web UI.  It should now be ready for use.

   """ % (CONFIG_FILE, CONFIG_FILE)

   return success(0)


def register_rpc(handlers):
   handlers["config_list"] = config_list
   handlers["config_reset"] = config_reset




