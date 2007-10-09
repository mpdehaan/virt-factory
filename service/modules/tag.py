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
from fieldvalidator import FieldValidator

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
                        "tag_get": self.get,
                        "tag_add": self.add,
                        "tag_edit": self.edit,
                        "tag_delete": self.delete}
        web_svc.AuthWebSvc.__init__(self)

    def get_tags_internal(self, module_obj, module_key, id_key, tag_dict):
        item_list = module_obj.list(None, {})
        for item in item_list.data:
            tags = item["tags"]
            for tag_name in tags:
                if not tag_dict.has_key(tag_name):
                    tag_dict[tag_name]={"id": tag_name,
                                        "name": tag_name,
                                        "machines": [],
                                        "machine_ids": [],
                                        "deployments": [],
                                        "deployment_ids": [] }
                tag_dict[tag_name][module_key].append(item)
                tag_dict[tag_name][id_key].append(item["id"])
        return tag_dict

    def get_tag_dict(self):
        tag_dict = self.get_tags_internal(machine.Machine(), "machines", "machine_ids", {})
        tag_dict = self.get_tags_internal(deployment.Deployment(), "deployments", "deployment_ids", tag_dict)
        return tag_dict
        
    def get(self, token, args={}):
        """
        Get a tag by name.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of tag attributes.
            - id
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
        tag_dict = self.get_tag_dict()
        if not tag_dict.has_key(args["name"]):
            raise NoSuchObjectException(comment='tag %s not found' % args["name"])
        return success(self.get_tag_dict()[args["name"]])
        
    def list(self, token, args={}):
        """
        Returns a list of tags with associated machines and deployments
        """
        return success(self.get_tag_dict().values())
        
    def get_tag_names(self, token, args={}):
        return success(self.get_tag_dict().keys())
        
    def add(self, token, args):
        """
        Create a tag
        @param token: A security token.
        @type token: string
        @param args: A dictionary of tag attributes.
        @type args: dict
            - id
            - name
            - machine_ids
            - deployment_ids
        @raise SQLException: On database error
        """
        # also accept id for name to make WUI happy
        if args.has_key('id') and (not args.has_key('name')):
            args["name"]=args["id"]
        required = ('name',)
        optional = ('machine_ids', 'deployment_ids')
        FieldValidator(args).verify_required(required)
        name = args["name"]
        machine_ids = []
        deployment_ids = []
        if args.has_key('machine_ids'):
            machine_ids = args['machine_ids']
        if args.has_key('deployment_ids'):
            deployment_ids = args['deployment_ids']
        if name in self.get_tag_names(token).data:
            raise InvalidArgumentsException(comment='tag %s already exists' % name)
        machine_obj = machine.Machine()
        deployment_obj = deployment.Deployment()
        for machine_id in machine_ids:
            machine_obj.add_tag(token, {"id": machine_id, "tag": name})
        for deployment_id in deployment_ids:
            deployment_obj.add_tag(token, {"id": deployment_id, "tag": name})
        return success()
         
    def edit(self, token, args):
        """
        Edit a tag
        @param token: A security token.
        @type token: string
        @param args: A dictionary of tag attributes.
        @type args: dict
            - id
            - name
            - machine_ids
            - deployment_ids
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        # also accept id for name to make WUI happy
        if args.has_key('id') and (not args.has_key('name')):
            args["name"]=args["id"]
        required = ('name',)
        optional = ('machine_ids', 'deployment_ids')
        FieldValidator(args).verify_required(required)
        name = args["name"]
        machine_ids = []
        deployment_ids = []
        db_machine_ids = []
        db_deployment_ids = []
        if args.has_key('machine_ids'):
            machine_ids = args['machine_ids']
        if args.has_key('deployment_ids'):
            deployment_ids = args['deployment_ids']
        tag_in_db = self.get(token, {"name":  name}).data
        machine_obj = machine.Machine()
        deployment_obj = deployment.Deployment()

        # loop through current machines for this tag -- remove
        # any that are not in the new list
        for db_machine in tag_in_db["machines"]:
            this_id = db_machine["id"]
            db_machine_ids.append(this_id)
            if this_id not in machine_ids:
                machine_obj.remove_tag(token, {"id": this_id, "tag": name})

        # loop through current deployments for this tag -- remove
        # any that are not in the new list
        for db_deployment in tag_in_db["deployments"]:
            this_id = db_deployment["id"]
            db_deployment_ids.append(this_id)
            if this_id not in deployment_ids:
                deployment_obj.remove_tag(token, {"id": this_id, "tag": name})
            
        # loop through new machines for this tag -- add
        # any that are not in the current list
        for machine_id in machine_ids:
            if machine_id not in db_machine_ids:
                machine_obj.add_tag(token, {"id": machine_id, "tag": name})

        # loop through new deployments for this tag -- add
        # any that are not in the current list
        for deployment_id in deployment_ids:
            if deployment_id not in db_deployment_ids:
                deployment_obj.add_tag(token, {"id": deployment_id, "tag": name})
                
        return success()
         
    def delete(self, token, args):
        """
        Deletes a tag.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of user attributes.
            - id
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        if args.has_key('id') and (not args.has_key('name')):
            args["name"]=args["id"]
        return self.edit(token, {"name": args["name"], "deployment_ids": [], "machine_ids": []})



methods = Tag()
register_rpc = methods.register_rpc



