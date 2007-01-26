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

import string
import machine

from codes import *
import web_svc

class Puppet(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"puppet_node_info": self.node_info}
        web_svc.AuthWebSvc.__init__(self)

    def node_info(self, token, puppet_args):
         """
         Returns parent node and class list for a given puppet node.
         """
         nodename = puppet_args["nodename"]
         found_node = None
         machine_obj = machine.Machine()
         machine_list_return = machine_obj.list(None, {})
         if (machine_list_return.error_code != ERR_SUCCESS):
             return machine_list_return

         for this_machine in machine_list_return.data:
             if this_machine["address"] == nodename:
                 found_node = this_machine
                 break

         data = {}
         if found_node is not None:
             image = found_node["image"]
             if image is not None:
                 puppet_str = image["puppet_classes"]
                 if puppet_str is not None:
                     puppet_classes = puppet_str.split()
                 else:
                     puppet_classes = []
             else:
                 puppet_classes = []
             if "puppet_node_diff" in found_node:
                 override_str = found_node["puppet_node_diff"]
                 if (override_str is not None):
                     for override in override_str.split():
                         if (override[0] == '-'):
                             override = override[1:]
                             if override in puppet_classes:
                                 puppet_classes.remove(override)
                         else:
                             if override not in puppet_classes:
                                 puppet_classes.append(override)

         else:
             #FIXME: check deployments here
             return NoSuchObjectException()
         data["puppet_classes"] = puppet_classes
         #data["parent"] = foo
         return success(data)


methods = Puppet()
register_rpc = methods.register_rpc



