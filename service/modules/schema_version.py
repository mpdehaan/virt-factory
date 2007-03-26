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

class SchemaVersionData(baseobj.BaseObject):

    FIELDS = [ "id", "version", "git_tag", "install_timestamp", "status", "notes"]

    def _produce(klass, dist_args,operation=None):
        """
        Factory method.  Create a schema version object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the schema version object.
        """

        self = SchemaVersionData()
        self.from_datastruct(dist_args)
        self.validate(operation)
        return self

    produce = classmethod(_produce)

    def from_datastruct(self,dist_args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the schema version as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        schema version object for interaction with the ORM.  See methods below for examples.
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
            # version is a positive int
            if self.version and not type(self.version) == int and self.version > 0:
                invalid_fields["version"] = REASON_FORMAT
      
            # git_tag is printable
            if (self.git_tag is not None) and (not self.is_printable(self.git_tag)):
                invalid_fields["git_tag"] = REASON_FORMAT
      
            # status is one of the architecture constants in codes.py
            if not self.status in VALID_SCHEMA_VERSION_STATUS:
                invalid_fields["status"] = REASON_RANGE   

            # notes is printable
            if (self.notes is not None) and (not self.is_printable(self.notes)):
                invalid_fields["notes"] = REASON_FORMAT
      

        if len(invalid_fields) != 0:
            print "Invalid fields: ", invalid_fields
            raise InvalidArgumentsException(invalid_fields=invalid_fields)


class SchemaVersion(web_svc.AuthWebSvc):

    DB_SCHEMA = {
        "table" : "schema_versions",
        "fields" : SchemaVersionData.FIELDS,
        "add"    : [ "version", "git_tag", "install_timestamp", "status", "notes" ],
        "edit"   : [ "status", "notes" ]
        }


    def __init__(self):
        self.methods = {"schema_version_add"    : self.add,
                        "schema_version_delete" : self.delete,
                        "schema_version_edit"   : self.edit,
                        "schema_version_list"   : self.list,
                        "schema_version_get"    : self.get}
        web_svc.AuthWebSvc.__init__(self)

        # FIXME: could go in the baseclass...
        self.db.db_schema = self.DB_SCHEMA

    def add(self, token, args):

        u = SchemaVersionData.produce(args,OP_ADD)
        result = self.db.simple_add(u.to_datastruct())
        return result

    def edit(self, token, args): 

        u = SchemaVersionData.produce(args,OP_EDIT)
        # TODO: make this work w/ u.to_datastruct() 
        result = self.db.simple_edit(args)
        return result

    def delete(self, token, args):

        u = SchemaVersionData.produce(args,OP_DELETE) # force validation
        return self.db.simple_delete(u.to_datastruct())


    def list(self, token, args):
        """
        Return a list of schema versions.  The dist_args list is currently *NOT*
        used.  Ideally we need to include LIMIT information here for
        GUI pagination when we start worrying about hundreds of systems.
        """

        return self.db.simple_list(args)


    def get(self, token, args):
        """
        Return a specific schema version record.  Only the "id" is required in dist_args.
        """
        
        u = SchemaVersionData.produce(args,OP_GET) # force validation
        return self.db.simple_get(u.to_datastruct())

    def get_by_version(self, token, args):
        """
        Return a specific schema version record by version name. Only the "version" is required
        in dist_args.
        """

        if args.has_key("version"):
            version = args["version"]
        else:
            raise ValueError("version is required")
            
        result = self.db.simple_list({}, {"version": "'%s'" % version})
        if (len(result.data) > 0):
            return success(result.data[0])
        else:
            return NoSuchObjectException(comment="get_by_verion")

    def get_current_version(self, token):
        """
        Return the most recent schema version.
        """

        result = self.db.simple_list({}, {"status": "'%s'" % SCHEMA_VERSION_END},
                                     order_by_str="install_timestamp desc")
        if (len(result.data) > 0):
            return success(result.data[0])
        else:
            return NoSuchObjectException(comment="get_current_verion")


methods = SchemaVersion()
register_rpc = methods.register_rpc

