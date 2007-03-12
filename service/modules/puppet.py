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

from server.codes import *

from datetime import *
import os
import string
import time
import machine
import deployment

import web_svc

PUPPETCA = "/usr/sbin/puppetca"

class Puppet(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"puppet_node_info": self.node_info,
                        "sign_node_cert": self.sign_node_cert}
        web_svc.AuthWebSvc.__init__(self)

    def node_info(self, token, puppet_args):
        """
        Returns parent node and class list for a given puppet node.
        """
        nodename = puppet_args["nodename"]
        found_node = None
        deployment_obj = deployment.Deployment()
        deployment_list_return = deployment_obj.get_by_hostname(None, {"hostname": nodename})
        if (deployment_list_return.error_code != ERR_SUCCESS):
            return deployment_list_return

        # TODO: should we complain if more than 1 deployments are returned?
        if (len(deployment_list_return.data) > 0):
            found_node = deployment_list_return.data[0]

        # if no deployment found, search for machine
        if (found_node is None):
            machine_obj = machine.Machine()
            machine_list_return = machine_obj.get_by_hostname(None, {"hostname": nodename})
            if (machine_list_return.error_code != ERR_SUCCESS):
                return machine_list_return

            # TODO: should we complain if more than 1 machines are returned?
            if (len(machine_list_return.data) > 0):
                found_node = machine_list_return.data[0]


        data = {}
        if found_node is not None:
            profile = found_node["profile"]
            if profile is not None:
                puppet_str = profile["puppet_classes"]
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

    def sign_node_cert(self, token, nodename, timeout=60):
        """
        calls puppetca to sign pending client certificate
        """
        now = datetime.now()
        timeout = now+timedelta(seconds=timeout)
        
        # waiting for incoming request
        found = self.check_for_cert_request(nodename)
        while ((datetime.now() < timeout) and (not found)):
            print "sleeping.."
            time.sleep(2)
            found = self.check_for_cert_request(nodename)

        if (not found):
            # don't fail here -- running register for already-signed cert should succeed
            return success()
#            raise PuppetNodeNotSignedException(comment="timeout reached: no pending requests for " + nodename)

        return_code = os.system(PUPPETCA + " -s " + nodename)
        signal = return_code & 0xFF
        exitcode = (return_code >> 8) & 0xFF
        if exitcode:
            raise PuppetNodeNotSignedException(comment="puppetca error, exit code: " + exitcode)
        return success()

    def check_for_cert_request(self, nodename):
        pipe = os.popen(PUPPETCA + " -l")
        found = 0
        for line in pipe.readlines():
            if line.strip() == nodename:
                found = 1
        closed = pipe.close()
        #if (closed is None):
        #    print "normal return"
        #else:
        #    print "list close: " +closed
        #if (found):
        #    print "node " + nodename + " has a waiting request"
        #else:
        #    print "no waiting request for " + nodename
        return found

methods = Puppet()
register_rpc = methods.register_rpc



