#!/usr/bin/python
## ShadowManager backend code.
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

from codes import *

import baseobj
import provisioning
import web_svc

import os
import traceback
import threading


#------------------------------------------------------------

class DistributionData(baseobj.BaseObject):

    FIELDS = [ "id", "kernel", "initrd", "options", "kickstart", "name",
               "architecture", "kernel_options", "kickstart_metadata" ]

    def _produce(klass, dist_args,operation=None):
        """
        Factory method.  Create a distribution object from input data, optionally
        running it through validation, which will vary depending on what
        operation is creating the distribution object.
        """

        self = DistributionData()
        self.from_datastruct(dist_args)
        self.validate(operation)
        return self

    produce = classmethod(_produce)

    def from_datastruct(self,dist_args):
        """
        Helper method to fill in the object's internal variables from
        a hash.  Note that we *don't* want to do this and then call
        session.save on the distribution as the junk fields like the "-1" would be 
        propogated.  It's best to use this for validation and build a *second*
        distribution object for interaction with the ORM.  See methods below for examples.
        """

        return self.deserialize(dist_args) # ,self.FIELDS)

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
            # TODO
            # kernel references file on filesystem
            if not os.path.isfile(self.kernel):
                invalid_fields["kernel"] = REASON_NOFILE

            # initrd references file on filesystem
            if not os.path.isfile(self.initrd):
                invalid_fields["initrd"] = REASON_NOFILE

            if (self.kickstart is not None) and (not os.path.isfile(self.kickstart)):
                invalid_fields["kickstart"] = REASON_NOFILE

            # name is printable
            # FIXME: this is lame, replace with regex module stuff later.
            if (self.kernel_options is not None) and (not self.is_printable(self.kernel_options)):
                invalid_fields["name"] = REASON_FORMAT
      
            # architecture is one of the architecture constants in codes.py
            if not self.architecture in VALID_ARCHS:
                invalid_fields["architecture"] = REASON_RANGE   

            # kernel options is printable, space delimited a=b pairs 
            if (self.kernel_options is not None) and (not self.is_printable(self.kernel_options)):
                invalid_fields["kernel_options"] = REASON_FORMAT

        # kickstart metadata is composed of space delimited a=b pairs, or None/blank

        if len(invalid_fields) != 0:
            print "Invalid fields: ", invalid_fields
            raise InvalidArgumentsException(invalid_fields=invalid_fields)


class Distribution(web_svc.AuthWebSvc):

    DB_SCHEMA = {
        "table" : "distributions",
        "fields" : DistributionData.FIELDS,
        "add"   : [ "kernel", "initrd", "options", "kickstart", "name", "architecture",
                    "kernel_options", "kickstart_metadata" ],
        "edit"  : [ "kernel", "initrd", "kickstart", "name", "architecture",
                    "kernel_options", "kickstart_metadata" ]
        }


    def __init__(self):
        self.methods = {"distribution_add"    : self.add,
                        "distribution_delete" : self.delete,
                        "distribution_edit"   : self.edit,
                        "distribution_list"   : self.list,
                        "distribution_get"    : self.get}
        web_svc.AuthWebSvc.__init__(self)

        # FIXME: could go in the baseclass...
        self.db.db_schema = self.DB_SCHEMA

    def add(self, token, dist_args):
        """
        Create a distribution.  dist_args should contain all distribution fields except ID.
        """

        u = DistributionData.produce(dist_args,OP_ADD)
        result = self.db.simple_add(u.to_datastruct())
        self.sync()
        return result

    def sync(self):
        self.provisioning = provisioning.Provisioning()
        self.provisioning.sync(None, {} )
        
    def edit(self, token, dist_args): 

        u = DistributionData.produce(dist_args,OP_EDIT)
        # TODO: make this work w/ u.to_datastruct() 
        result = self.db.simple_edit(dist_args)
        self.sync()
        return result

    def delete(self, token, dist_args):

        st = """
        SELECT images.id FROM images, distributions WHERE
        images.distribution_id = :id
        """

        u = DistributionData.produce(dist_args, OP_DELETE)
        self.db.cursor.execute(st, u.to_datastruct())
        x = self.db.cursor.fetchone()
        if x is not None:
            raise OrphanedObjectException(comment="images.distribution_id")
        u = DistributionData.produce(dist_args,OP_DELETE) # force validation
        
        return self.db.simple_delete(u.to_datastruct())


    def list(self, token, dist_args):
        """
        Return a list of distributions.  The dist_args list is currently *NOT*
        used.  Ideally we need to include LIMIT information here for
        GUI pagination when we start worrying about hundreds of systems.
        """

        return self.db.simple_list(dist_args)


    def get(self, token, dist_args):
        """
        Return a specific distribution record.  Only the "id" is required in dist_args.
        """
        
        u = DistributionData.produce(dist_args,OP_GET) # force validation
        return self.db.simple_get(u.to_datastruct())

    def get_by_name(self, token, dist_args):
        """
        Return a specific distribution record by name. Only the "name" is required
        in dist_args.
        """

        if dist_args.has_key("name"):
            name = dist_args["name"]
        else:
            raise ValueError("name is required")
            
        result = self.db.simple_list({}, {"name": name})
        if (len(result.data) == 1):
            return success(result.data[0])
        else:
            return NoSuchObjectException(comment="get_by_name")


methods = Distribution()
register_rpc = methods.register_rpc
