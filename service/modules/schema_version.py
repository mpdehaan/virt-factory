#!/usr/bin/python
## Virt-factory backend code.
##
## Copyright 2007, Red Hat, Inc
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

import web_svc

import os
import traceback
import threading


class SchemaVersion(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"schema_version_add"    : self.add,
                        "schema_version_delete" : self.delete,
                        "schema_version_edit"   : self.edit,
                        "schema_version_list"   : self.list,
                        "schema_version_get"    : self.get}
        web_svc.AuthWebSvc.__init__(self)


    def add(self, token, args):
        """
        Create a schema version.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of schema version attributes.
        @type args: dict
            - version
            - git_tag (optional)
            - install_timestamp (optional)
            - status (optional)
            - notes (optional)
        @raise SQLException: On database error
        """
        required = ('version',)
        optional = ('git_tag', 'install_timestamp', 'status', 'notes')
        self.validate(args, required)
        session = db.open_session()
        try:
            schema_version = db.SchemaVersion()
            schema_version.update(args)
            session.save(schema_version)
            session.flush()
            return success(schema_version.id)
        finally:
            session.close()


    def edit(self, token, args): 
        """
        Edit a schema version.
        @param token: Security token.
        @type token: string
        @param args: A dictionary of schema version attributes.
        @type args: dict
            - id
            - status (optional)
            - notes (optional)
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        optional = ('status', 'notes')
        filter = ('id', 'version', 'git_tag', 'install_timestamp')
        self.validate(args, required)
        session = db.open_session()
        try:
            schema_version = db.SchemaVersion.get(session, args['id'])
            schema_version.update(args, filter)
            session.save(schema_version)
            session.flush()
            return success()
        finally:
            session.close()


    def delete(self, token, args):
        """
        Delete a schema version.
        @param token: Security token.
        @type token: string
        @param args: A dictionary of schema version attributes.
        @type args: dict
            - id
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            db.SchemaVersion.delete(session, args['id'])
            return success()
        finally:
            session.close()


    def list(self, token, args):
        """
        Get all schema versions.
        @param token: Security token.
        @type token: string
        @param args: A dictionary of schema version attributes.
        @type args: dict
           - offset (optional)
           - limit (optional)
        @return: A list of schema versions..
        @rtype: [dict,]
            - id
            - version
            - git_tag (optional)
            - install_timestamp (optional)
            - status (optional)
            - notes (optional)
        @raise SQLException: On database error
        """
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            for sv in db.SchemaVersion.list(session, offset, limit):
                result.append(sv.data())
            return success(result)
        finally:
            session.close()


    def get(self, token, args):
        """
        Get a schema version by id.
        @param token: Security token.
        @type token: string
        @param args: A dictionary of schema version attributes.
            - id
        @type args: dict
        @return: A schema version.
        @rtype: dict
            - id
            - version
            - git_tag (optional)
            - install_timestamp (optional)
            - status (optional)
            - notes (optional)
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            sv = db.SchemaVersion.get(session, args['id'])
            return success(sv.data())
        finally:
            session.close()


    def get_by_version(self, token, args):
        """
        Get a schema version by version.
        @param token: A security token.
        @type token: string
        @param args: The version.
        @type args: dict 
            - version
        @return: A profile.
        @rtype: dict
            - id
            - version
            - git_tag (optional)
            - install_timestamp (optional)
            - status (optional)
            - notes (optional)
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('name',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            version = args['version']
            query = session.query(db.SchemaVersion)
            sv = query.selectfirst_by(version == version, order_by=[desc(SchemaVersion.c.id),])
            if sv is None:
                 raise NoSuchObjectException(comment=version)
            return success(sv.data())
        finally:
            session.close()


    def get_current_version(self, token):
        """
        Get the most recent schema version.
        @param token: A security token.
        @type token: string
        @param args: (not used).
        @type args: dict 
        @return: A profile.
        @rtype: dict
            - id
            - version
            - git_tag (optional)
            - install_timestamp (optional)
            - status (optional)
            - notes (optional)
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('name',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            query = session.query(db.SchemaVersion)
            sv = query.selectfirst(order_by=[desc(SchemaVersion.c.id),])
            if sv is None:
                 raise NoSuchObjectException(comment=version)
            return success(sv.data())
        finally:
            session.close()

           
    def validate(self, args, required):
        vdr = FieldValidator(args)
        vdr.verify_required(required)
        vdr.verify_int('version')
        vdr.verify_enum('status', VALID_SCHEMA_VERSION_STATUS)
        vdr.verify_printable('git_tag', 'notes')


methods = SchemaVersion()
register_rpc = methods.register_rpc

