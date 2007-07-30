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
from server import db
from server import config_data
from fieldvalidator import FieldValidator
import distribution
import cobbler
import provisioning
import web_svc

import os
import threading
import traceback


class Profile(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"profile_add": self.add,
                        "profile_edit": self.edit,
                        "profile_delete": self.delete,
                        "profile_get": self.get,
			"profile_get_by_name": self.get_by_name,
                        "profile_list": self.list}
        web_svc.AuthWebSvc.__init__(self)


    def add(self, token, args):
        """
        Create a profile.
        @param token: A security token.
        @type token: string
        @param args: Profile attributes.
        @type args: dict 
        @raise SQLException: On database error
        """
        optional =\
            ('distribution_id', 'virt_storage_size', 'virt_ram', 'virt_type', 
             'kickstart_metadata',
             'kernel_options', 'puppet_classes')
        required = ('name', 'version', 'valid_targets', 'is_container')
        self.validate(args, required)
        session = db.open_session()
        try:
            profile = db.Profile()
            profile.update(args)
            session.save(profile)
            session.flush()
            self.cobbler_sync(profile.get_hash())
        finally:
            session.close()

         
    def cobbler_sync(self, data):
         # make the corresponding cobbler calls.
         cobbler_api = config_data.Config().cobbler_api
         distributions = distribution.Distribution().list(None, {}).data
         provisioning.CobblerTranslatedProfile(cobbler_api ,distributions, data)


    def edit(self, token, args):
        """
        Edit a profile.
        @param token: A security token.
        @type token: string
        @param args: profile attributes.
        @type args: dict 
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        optional =\
            ('name', 'version', 'valid_targets', 'is_container', 'distribution_id', 'virt_storage_size', 
             'virt_ram', 'virt_type', 'kickstart_metadata', 'kernel_options', 'puppet_classes')
        self.validate(args, required)
        session = db.open_session()
        try:
            profile = db.Profile.get(session, args['id'])
            profile.update(args)
            session.save(profile)
            session.flush()
            return success()
        finally:
            session.close()


    def delete(self, token, args):
        """
        Delete a profile.
        @param token: A security token.
        @type token: string
        @param args: The profile id to be deleted.
        @type args: dict 
            - id
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            db.Profile.delete(session, args['id'])
            return success()
        finally:
            session.close()


    def list(self, token, args):
        """
        Get a list of all profiles..
        @param token: A security token.
        @type token: string
        @param args: A dictionary of query properties.
        @type args: dict
            - offset (optional)
            - limit (optional)
        @return: A list of profiles.
        @rtype: [dict,]
        @raise SQLException: On database error
        """
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            for profile in db.Profile.list(session, offset, limit):
                result.append(self.expand(profile))
            return success(result)
        finally:
            session.close()


    def get(self, token, args):
        """
        Get a profile by id.
        @param token: A security token.
        @type token: string
        @param args: The profile id.
        @type args: dict 
            - id
        @return: A profile.
        @rtype: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.  
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            self.logger.info(args)
            profile = db.Profile.get(session, args['id'])
            return success(self.expand(profile))
        finally:
            session.close()


    def get_by_name(self, token, args):
        """
        Get a profile by name.
        @param token: A security token.
        @type token: string
        @param args: The profile name.
        @type args: dict 
            - name
        @return: A profile.
        @rtype: dict
        @raise SQLException: On database error
        """
        required = ('name',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            name = args['name']
            profile = session.query(db.Profile).selectfirst_by(name = name)
            if profile:
                profile = self.expand(profile)
            return success(profile)
        finally:
            session.close()


    def validate(self, args, required):
        vdr = FieldValidator(args)
        vdr.verify_required(required)
        vdr.verify_printable('name', 'version', 'kernel_options', 'puppet_classes', 'virt_type')
        vdr.verify_int(['virt_storage_size', 'virt_ram'])
        vdr.verify_enum('valid_targets', VALID_TARGETS)
        vdr.verify_enum('is_container', VALID_CONTAINERS)


    def expand(self, profile):
        result = profile.get_hash()
        result['distribution'] = profile.distribution.get_hash()
        return result


methods = Profile()
register_rpc = methods.register_rpc


