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
from server import codes
from server import db
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
                        "tag_get": self.get,
                        "tag_add": self.add,
                        "tag_edit": self.edit,
                        "tag_delete": self.delete}
        web_svc.AuthWebSvc.__init__(self)

    def get(self, token, args={}):
        """
        Get a tag by name.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of tag attributes.
            - id
        @type args: dict
        @return A tag
        @rtype: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            tag = db.Tag.get(session, args['id'])
            results = self.expand(tag)
            self.logger.info("your tag is: %s" % results)
            return success(results)

        finally:
            session.close()
        
    def list(self, token, args):
        """
        Get a list of all tags.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of tag attributes.
        @type args: dict
            - offset (optional)
            - limit (optional)
        @return A list of all tags.
        @rtype: [dict,]
        @raise SQLException: On database error
        """    
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            for tag in db.Tag.list(session, offset, limit):
                result.append(self.expand(tag))
            return codes.success(result)
        finally:
            session.close()

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
        required = ('name',)
        optional = ('machine_ids', 'deployment_ids')
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            tag = db.Tag()
            tag.update(args)
            session.save(tag)
            if args.has_key('machine_ids'):
                setattr(tag, "machines", self.objects_from_ids(session,
                                                               db.Machine,
                                                               args['machine_ids']))
            if args.has_key('deployment_ids'):
                setattr(tag, "deployments", self.objects_from_ids(session,
                                                                  db.Deployment,
                                                                  args['deployment_ids']))
            session.flush()
            return success()
        finally:
            session.close()
         
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
        required = ('id',)
        optional = ('name', 'machine_ids', 'deployment_ids')
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            tag = db.Tag.get(session, args['id'])
            tag.update(args)
            session.save(tag)
            if args.has_key('machine_ids'):
                setattr(tag, "machines", self.objects_from_ids(session,
                                                               db.Machine,
                                                               args['machine_ids']))
            if args.has_key('deployment_ids'):
                setattr(tag, "deployments", self.objects_from_ids(session,
                                                                  db.Deployment,
                                                                  args['deployment_ids']))
            session.flush()
            return success()
        finally:
            session.close()
         
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
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            db.Tag.delete(session, args['id'])
            return codes.success()
        finally:
            session.close()

    def tags_from_ids(self, session, tag_ids):
        return self.objects_from_ids(session, db.Tag, tag_ids)
            
    def objects_from_ids(self, session, type_obj, ids):
        objs = []
        for id in ids:
            objs.append(type_obj.get(session, id))
        return objs

    def expand(self, tag):
        result = tag.get_hash()
        result['machines'] = []
        result['machine_ids'] = []
        for machine in tag.machines:
            result['machines'].append(machine.get_hash())
            result['machine_ids'].append(machine.id)
        result['deployments'] = []
        result['deployment_ids'] = []
        for deployment in tag.deployments:
            deployment_hash = deployment.get_hash()
            deployment_hash["machine"] = deployment.machine.get_hash()
            deployment_hash["profile"] = deployment.profile.get_hash()
            result['deployments'].append(deployment_hash)
            result['deployment_ids'].append(deployment.id)
        return result


methods = Tag()
register_rpc = methods.register_rpc



