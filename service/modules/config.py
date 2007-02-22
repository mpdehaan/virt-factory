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
import config_data

import web_svc

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

class Config(web_svc.AuthWebSvc):
     def __init__(self):
        self.methods = {"config_list": self.list,
                        "config_reset": self.reset}
        web_svc.AuthWebSvc.__init__(self)
        config_data_obj = config_data.Config()
        self.config_data = config_data_obj.get()

     def list(self, config_args=None):

        return success(self.config_data)

     def reset(self, config_args=None):

        self.config_data.reset()
      
        print """
      The configuration values in %s have been reset.

      Next steps:
         (1) Edit the address field and mirror list in %s
             Change other settings as desired.
         (2) Run 'shadow import' to import distributions from your selected mirrors.
         (3) Test the configuration by logging in using the Web UI.  It should now be ready for use.

      """ % (CONFIG_FILE, CONFIG_FILE)

        return success(0)


methods = Config()
register_rpc = methods.register_rpc




