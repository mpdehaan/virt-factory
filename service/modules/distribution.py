#!/usr/bin/python
## Virt-factory backend code.
##
## Copyright 2006, Red Hat, Inc
## Michael DeHaan <mdehaan@redhat.com>
## Scott Seago <sseago@redhat.com>
## Adrian Likins <alikins@redhat.com>
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
##

from server.codes import *
from server import db
from fieldvalidator import FieldValidator

import provisioning
import cobbler
import web_svc
from server import config_data

import traceback
import threading



class Distribution(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"distribution_add"    : self.add,
                        "distribution_delete" : self.delete,
                        "distribution_edit"   : self.edit,
                        "distribution_list"   : self.list,
                        "distribution_get"    : self.get}
        web_svc.AuthWebSvc.__init__(self)


    def add(self, token, args):
        """
        Add a distribution.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of distribution properties.
        @type args: dict
            - kernel
            - initrd
            - options (optional)
            - kickstart  (optional)
            - name
            - architecture
            - kernel_options (optional)
            - kickstart_metadata (optional)
        @raise SQLException: On database error
        """
        required = ('kernel', 'initrd', 'name', 'architecture')
        optional = ('options', 'kickstart', 'kernel_options', 'kickstart_metadata')
        self.validate(args, required)
        session = db.open_session()
        try:
            distribution = db.Distribution()
            distribution.update(args)
            session.save(distribution)
            session.flush()
            self.cobbler_sync(distribution.get_hash())
        finally:
            session.close()


    def cobbler_sync(self, data):
         cobbler_api = config_data.Config().cobbler_api
         provisioning.CobblerTranslatedDistribution(cobbler_api, data)       
 
 
    def edit(self, token, args):
        """
        Add a distribution.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of distribution properties.
        @type args: dict
            - id
            - kernel  (optional)
            - initrd  (optional)
            - kickstart  (optional)
            - name  (optional)
            - architecture  (optional)
            - kernel_options (optional)
            - kickstart_metadata (optional)
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        optional = ('kernel', 'initrd', 'name', 'architecture', 'kickstart', 'kernel_options', 'kickstart_metadata')
        filter = ('id', 'options')
        self.validate(args, required)
        session = db.open_session()
        try:
            distribution = db.Distribution.get(session, args['id'])
            distribution.update(args, filter)
            session.save(distribution)
            session.flush()
            self.cobbler_sync(distribution.get_hash())
            return success()
        finally:
            session.close()


    def delete(self, token, args):
        """
        Deletes a distribution.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of distribution attributes.
            - id
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            db.Distribution.delete(session, args['id'])
            return success()
        finally:
            session.close()


    def list(self, token, args):
        """
        Get all distributions.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of distribution attributes.
        @type args: dict
            - offset (optional)
            - limit (optional)
        @return: A list of distributions.
        @rtype: [dict,]
           - id
           - kernel
           - initrd
           - options (optional)
           - kickstart  (optional)
           - name
           - architecture
           - kernel_options (optional)
           - kickstart_metadata (optional)
        @raise SQLException: On database error
        """
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            for distribution in db.Distribution.list(session, offset, limit):
                result.append(distribution.get_hash())
            return success(result)
        finally:
            session.close()


    def get(self, token, args):
        """
        Get all distributions.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of distribution attributes.
        @type args: dict
            - id
        @return: A distribution by id.
        @rtype: dict
           - id
           - kernel
           - initrd
           - options (optional)
           - kickstart  (optional)
           - name
           - architecture
           - kernel_options (optional)
           - kickstart_metadata (optional)
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            distribution = db.Distribution.get(session, args['id'])
            return success(distribution.get_hash())
        finally:
            session.close()


    def get_by_name(self, token, args):
        """
        Get all distributions.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of distribution attributes.
        @type args: dict
            - name
        @return: A distribution by name.
        @rtype: dict
           - id
           - kernel
           - initrd
           - options (optional)
           - kickstart  (optional)
           - name
           - architecture
           - kernel_options (optional)
           - kickstart_metadata (optional)
        @raise SQLException: On database error
        """
        required = ('name',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            name = args['name']
            distribution = session.query(db.Distribution).selectfirst_by(name = name)
            if distribution is None:
                raise NoSuchObjectException(comment="objectid")
            return success(distribution.get_hash())
        finally:
            session.close()


    def validate(self, args, required):
        vdr = FieldValidator(args)
        vdr.verify_required(required)
        vdr.verify_file('kernel', 'initrd')
        vdr.verify_printable('name', 'kernel_options')
        vdr.verify_enum('architecture', VALID_ARCHS)


methods = Distribution()
register_rpc = methods.register_rpc

