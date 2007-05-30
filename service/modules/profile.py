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
from server import config_data

import baseobj
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
                        "profile_list": self.list}
        web_svc.AuthWebSvc.__init__(self)


    def add(self, token, args):
        """
        Create a profile.
        @param args: Profile attributes.
        @type args: dict 
            - id,
            - name
            - version
            - distribution_id
            - virt_storage_size
            - virt_ram
            - kickstart_metadata
            - kernel_options
            - valid_targets
            - is_container
            - puppet_classes
        """
        optional =\
            ('distribution_id', 'virt_storage_size', 'virt_ram', 'kickstart_metadata',
             'kernel_options', 'puppet_classes')
        required = ('name', 'version', 'valid_targets', 'is_container')
        self.__validate(args, required)
        session = db.open_session()
        try:
            profile = db.Proflie()
            for key in (required+optional):
                setattr(profile, key, args.get(key, None))
            session.save(profile)
            session.flush()
            self.cobbler_sync(profile.data())
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
        @param args: profile attributes.
        @type args: dict 
            - id,
            - name (optional)
            - version (optional)
            - distribution_id (optional)
            - virt_storage_size (optional)
            - virt_ram (optional)
            - kickstart_metadata (optional)
            - kernel_options (optional)
            - valid_targets (optional)
            - is_container (optional)
            - puppet_classes (optional)
        """
        required = ('id')
        optional =\
            ('name', 'version', 'valid_targets', 'is_container', 'distribution_id', 'virt_storage_size', 
             'virt_ram', 'kickstart_metadata', 'kernel_options', 'puppet_classes')
        self.__validate(args, required)
        session = db.open_session()
        try:
            profileid = args['id']
            profile = session.get(db.Profile, profileid)
            if profile is None:
                 raise NoSuchObjectException(comment=profileid)
            for key in optional:
                setattr(profile, key, args.get(key, None))
            session.save(profile)
            session.flush()
            return success()
        finally:
            session.close()


    def delete(self, token, args):
        """
        Delete a profile.
        @param args: The profile id to be deleted.
        @type args: dict 
            - id
        """
        required = ('id')
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            profileid = args['id']
            profile = session.get(db.Profile, profileid)
            if profile is None:
                 raise NoSuchObjectException(comment=profileid)
            session.delete(profile)
            session.flush()
            return success()
        finally:
            session.close()


    def list(self, token, args):
        """
        Get a list of all profiles..
        @param args: not used.
        @type args: dict
        @return: A list of profiles.
        @rtype: [dict,]
            - id,
            - name (optional)
            - version (optional)
            - distribution_id (optional)
            - virt_storage_size (optional)
            - virt_ram (optional)
            - kickstart_metadata (optional)
            - kernel_options (optional)
            - valid_targets (optional)
            - is_container (optional)
            - puppet_classes (optional)
        # TODO: paging.
        # TODO: nested structures.  
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            for profile in session.query(db.Profile).select():
                result.append(profile.data())
            return success(result)
        finally:
            session.close()


    def get(self, token, args):
        """
        Get a profile by id.
        @param args: The profile id.
        @type args: dict 
            - id
        @return: A profile.
        @rtype: dict
            - id,
            - name (optional)
            - version (optional)
            - distribution_id (optional)
            - virt_storage_size (optional)
            - virt_ram (optional)
            - kickstart_metadata (optional)
            - kernel_options (optional)
            - valid_targets (optional)
            - is_container (optional)
            - puppet_classes (optional)
        # TODO: nested structures.            
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            profileid = args['id']
            profile = session.get(db.Profile, profileid)
            if profile is None:
                 raise NoSuchObjectException(comment=profileid)
            return success(profile.data())
        finally:
            session.close()


    def get_by_name(self, token, args):
        """
        Get a profile by id.
        @param args: The profile id.
        @type args: dict 
            - id
        @return: A profile.
        @rtype: dict
            - id,
            - name (optional)
            - version (optional)
            - distribution_id (optional)
            - virt_storage_size (optional)
            - virt_ram (optional)
            - kickstart_metadata (optional)
            - kernel_options (optional)
            - valid_targets (optional)
            - is_container (optional)
            - puppet_classes (optional)
        # TODO: nested structures. 
        """
        required = ('name',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            name = args['name']
            profile = session.query(db.Profile).selectfirst_by(name == name)
            if profile is None:
                 raise NoSuchObjectException(comment=name)
            return success(profile.data())
        finally:
            session.close()
            
    def __validate(self, args, required):
        validator = FieldValidator(args)
        validator.verify_required(required)
        validator.verify_printable('name', 'version')
        validator.verify_int('virt_storage_size', 'virt_ram', 'kernel_options', 'puppet_classes')
        validator.verify_enum('valid_targets', VALID_TARGETS)
        validator.verify_enum('is_container', VALID_CONTAINERS)


methods = Profile()
register_rpc = methods.register_rpc


