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

import baseobj
import provisioning
import cobbler
import web_svc

import os
import traceback
import threading


#------------------------------------------------------------

class UpgradeLogMessageData(baseobj.BaseObject):

    FIELDS = [ "id", "action", "message_type", "message_timestamp", "message"]

    def _produce(klass, dist_args,operation=None):
        """
        Factory method.  Create a upgrade log message object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the upgrade log message object.
        """

        self = UpgradeLogMessageData()
        self.from_datastruct(dist_args)
        self.validate(operation)
        return self

    produce = classmethod(_produce)

    def from_datastruct(self,dist_args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the upgrade log message as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        upgrade log message object for interaction with the ORM.  See methods below for examples.
        """

        return self.deserialize(dist_args)

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """

        return self.serialize()

    def validate(self,operation):

        invalid_fields = {} 

        if self.id is None:
            # -1 is for sqlite to say "use your own counter".
            self.id = -1 

        if operation in [OP_EDIT,OP_DELETE,OP_GET]:
            try:
                self.id = int(self.id)
            except:
                invalid_fields["id"] = REASON_FORMAT

        if operation in [OP_EDIT,OP_ADD]:
            # version is printable
            if (self.action is not None) and (not self.is_printable(self.action)):
                invalid_fields["action"] = REASON_FORMAT
      
            # message_type is one of the constants in codes.py
            if not self.message_type in VALID_UPGRADE_LOG_MESSAGE_STATUS:
                invalid_fields["message_type"] = REASON_RANGE   

            # message is printable
            if (self.message is not None) and (not self.is_printable(self.message)):
                invalid_fields["message"] = REASON_FORMAT
      

        if len(invalid_fields) != 0:
            #print "Invalid fields: ", invalid_fields
            raise InvalidArgumentsException(invalid_fields=invalid_fields)


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
        @param args: A dictionary of message attributes.
            - action (optional)
            - message_type
            - message (optional)
        @type args: dict
        """
        optional = ('action', 'message')
        required = ('message_type')
        validator = FieldValidator(args)
        validator.verify_required(required)
        session = db.open_session()
        try:
            msg = db.UpgradeLogMessage()
            for key in (required+optional):
                setattr(msg, key, args.get(key, None))
            session.save(msg)
            session.flush()
            return success(msg.id)
        finally:
            session.close()

    def edit(self, token, args):
        """
        Edit a message.
        @param args: A dictionary of message attributes.
        @type args: dict
            - id
            - action (optional)
            - message_type (optional)
            - message (optional)
        """
        required = ('id',)
        validator.verify_required(required)
        session = db.open_session()
        try:
            objectid = args['id']
            msg = session.get(db.UpgradeLogMessage, objectid)
            if msg is None:
                raise NoSuchObjectException(comment=objectid)
            for key in optional:
                current = getattr(msg, key)
                setattr(msg, key, args.get(key, current))
            session.save(msg)
            session.flush()
            return success()
        finally:
            session.close()


    def delete(self, token, args):
        """
        Delete a message.
        @param args: A dictionary of message attributes.
        @type args: dict
            - id
            - action (optional)
            - message_type (optional)
            - message (optional)
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            objectid = args['id']
            msg = session.get(db.UpgradeLogMessage, objectid)
            if msg is None:
                raise NoSuchObjectException(comment=objectid)
            session.delete(msg)
            session.flush()
            return success()
        finally:
            session.close()


    def list(self, token, args):
         """
         Get all messages.
         @param args: A dictionary of message attributes.
         @type args: dict
         @return: A list of messages.
         @rtype: [dict,]  
            - id
            - action (optional)
            - message_type (optional)
            - message_timestamp
            - message (optional)
         """
         session = db.open_session()
         try:
             result = []
             offset, limit = self.offset_and_limit(args)
             for msg in session.query(db.UpgradeLogMessage).select(offset=offset, limit=limit):
                 result.append(msg.date())
             return success(result)
         finally:
             session.close()


    def get(self, token, args):
         """
         Get a message by id.
         @param args: A dictionary of message attributes.
             - id
         @type args: dict
         @return: A messages.
         @rtype: dict
            - id
            - action (optional)
            - message_type (optional)
            - message_timestamp
            - message (optional)
         """
         required = ('id',)
         FieldValidator(args).verify_required(required)
         session = db.open_session()
         try:
             objectid = args['id']
             msg = session.get(db.UpgradeLogMessage, objectid)
             if msg is None:
                 raise NoSuchObjectException(comment=objectid)
             return success(msg.data())
         finally:
             session.close()


methods = UpgradeLogMessage()
register_rpc = methods.register_rpc

