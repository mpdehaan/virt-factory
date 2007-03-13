"""
Virt-factory backend code.

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
from server import yaml
from server.codes import *

from server import config_data
import web_svc

CONFIG_FILE = "/var/lib/virt-factory/settings"

# note: if the user rsync's too close the arch info won't be in the path,
# and this means we can't fill in the arch.  so the defaults probably
# slurp a bit too much default info but at least it's not pulling in
# all the FC's.

class Config(web_svc.AuthWebSvc):
     def __init__(self):
        self.methods = { "config_list": self.list }
        web_svc.AuthWebSvc.__init__(self)
        config_data_obj = config_data.Config()
        self.config_data = config_data_obj.get()

     def list(self, config_args=None):
        return success(self.config_data)


methods = Config()
register_rpc = methods.register_rpc




