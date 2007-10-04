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
import machine
import deployment

import web_svc

class Tag(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"tag_list": self.list,
                        "tag_get_names": self.get_tag_names,
                        "tag_get": self.get}
        web_svc.AuthWebSvc.__init__(self)

    def get_tags_internal(self, module_obj, module_key, tag_dict):
        item_list = module_obj.list(None, {})
        for item in item_list.data:
            tags = item["tags"]
            for tag_name in tags:
                if not tag_dict.has_key(tag_name):
                    tag_dict[tag_name]={"id": tag_name,
                                        "name": tag_name,
                                        "machines": [],
                                        "deployments": [] }
                tag_dict[tag_name][module_key].append(item)
        return tag_dict

    def get_tag_dict(self):
        tag_dict = self.get_tags_internal(machine.Machine(), "machines", {})
        tag_dict = self.get_tags_internal(deployment.Deployment(), "deployments", tag_dict)
        return tag_dict
        
    def get(self, token, args={}):
        """
        Get a tag by name.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of tag attributes.
            - name
        @type args: dict
        @return A tag
        @rtype: dict
        @raise NoSuchObjectException: On object not found.
        """
        # also accept id for name to make WUI happy
        if args.has_key('id') and (not args.has_key('name')):
            args["name"]=args["id"]
        required = ('name',)
        FieldValidator(args).verify_required(required)
        return success(self.get_tag_dict()[args["name"]])
        
    def list(self, token, args={}):
        """
        Returns a list of tags with associated machines and deployments
        """
        return success(self.get_tag_dict().values())
        
    def get_tag_names(self, token, args={}):
        return success(self.get_tag_dict().keys())
        

methods = Tag()
register_rpc = methods.register_rpc



