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
from baseobj import FieldValidator

import provisioning
import cobbler
import web_svc

import os
import traceback
import threading


class UpgradeLogMessage(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"upgrade_log_message_add"    : self.add,
                        "upgrade_log_message_delete" : self.delete,
                        "upgrade_log_message_edit"   : self.edit,
                        "upgrade_log_message_list"   : self.list,
                        "upgrade_log_message_get"    : self.get}
        web_svc.AuthWebSvc.__init__(self)


    def add(self, token, args):
        """
        Create a message.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of message attributes.
            - action (optional)
            - message_type
            - message (optional)
        @type args: dict
        @raise SQLException: On database error
        """
        optional = ('action', 'message')
        required = ('message_type')
        validator = FieldValidator(args)
        validator.verify_required(required)
        validator.verify_enum('message_type', VALID_UPGRADE_LOG_MESSAGE_STATUS)
        validator.verify_printable('action', 'message')
        session = db.open_session()
        try:
            msg = db.UpgradeLogMessage()
            msg.update(args)
            session.save(msg)
            session.flush()
            return success(msg.id)
        finally:
            session.close()


    def edit(self, token, args):
        """
        Edit a message.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of message attributes.
        @type args: dict
            - id
            - action (optional)
            - message_type (optional)
            - message (optional)
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        validator.verify_required(required)
        validator.verify_enum('message_type', VALID_UPGRADE_LOG_MESSAGE_STATUS)
        validator.verify_printable('action', 'message')
        session = db.open_session()
        try:
            msg = db.UpgradeLogMessage.get(session, args['id'])
            msg.update(args)
            session.save(msg)
            session.flush()
            return success()
        finally:
            session.close()


    def delete(self, token, args):
        """
        Delete a message.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of message attributes.
        @type args: dict
            - id
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            db.UpgradeLogMessage.delete(session, args['id'])
            return success()
        finally:
            session.close()


    def list(self, token, args):
        """
        Get all messages.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of message attributes.
        @type args: dict
           - offset (optional)
           - limit (optional)
        @return: A list of messages.
        @rtype: [dict,]  
           - id
           - action (optional)
           - message_type
           - message_timestamp
           - message (optional)
        @raise SQLException: On database error
        """
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            for msg in db.UpgradeLogMessage.list(session, offset, limit):
                result.append(msg.data())
            return success(result)
        finally:
            session.close()


    def get(self, token, args):
        """
        Get a message by id.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of message attributes.
            - id
        @type args: dict
        @return: A message.
        @rtype: dict
           - id
           - action (optional)
           - message_type
           - message_timestamp
           - message (optional)
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            msg = db.UpgradeLogMessage.get(session, args['id'])
            return success(msg.data())
        finally:
            session.close()


methods = UpgradeLogMessage()
register_rpc = methods.register_rpc

