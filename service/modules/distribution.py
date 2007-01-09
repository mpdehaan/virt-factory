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

        self.id                 = self.load(dist_args,"id")
        self.kernel             = self.load(dist_args,"kernel")
        self.initrd             = self.load(dist_args,"initrd")
        self.kickstart          = self.load(dist_args,"kickstart")
        self.name               = self.load(dist_args,"name")
        self.architecture       = self.load(dist_args,"architecture") 
        self.kernel_options     = self.load(dist_args,"kernel_options")
        self.kickstart_metadata = self.load(dist_args,"kickstart_metadata")

    def to_datastruct_internal(self):
        """
        Serialize the object for transmission over WS.
        """

        return {
            "id"                 : self.id,
            "kernel"             : self.kernel,
            "initrd"             : self.initrd,
            "kickstart"          : self.kickstart,
            "name"               : self.name,
            "architecture"       : self.architecture,
            "kernel_options"     : self.kernel_options,
            "kickstart_metadata" : self.kickstart_metadata
        }

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
            raise InvalidArgumentsException(invalid_fields=invalid_fields)


class Distribution(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"distribution_add": self.add,
                        "distribution_delete": self.delete,
                        "distribution_edit": self.edit,
                        "distribution_list": self.list,
                        "distribution_get": self.get}
        web_svc.AuthWebSvc.__init__(self)


    def add(self, token, dist_args):
         """
         Create a distribution.  dist_args should contain all distribution fields except ID.
         """

         u = DistributionData.produce(dist_args,OP_ADD)

         st = """
         INSERT INTO distributions (
         kernel, 
         initrd, 
         kickstart, 
         name, 
         architecture, 
         kernel_options, 
         kickstart_metadata)
         VALUES (
         :kernel,
         :initrd,
         :kickstart,
         :name, 
         :architecture,
         :kernel_options, 
         :kickstart_metadata)
         """

         lock = threading.Lock()
         lock.acquire()

         try:
             self.db.cursor.execute(st, u.to_datastruct())
             self.db.connection.commit()
         except Exception:
             lock.release()
             tb = traceback.format_exc()
             raise SQLException(traceback=tb)

         rowid = self.db.cursor.lastrowid
         lock.release()
         self.sync( {} )

         return success(rowid)

    def sync(self):
        if not self.provisioning:
            self.provisioning = provisioning.Provisioning()
        self.provisioning.sync( {} )
        
    def edit(self, token, dist_args): 

         u = DistributionData.produce(dist_args,OP_EDIT)

         st = """
         UPDATE distributions SET
         kernel=:kernel,
         initrd=:initrd,
         kickstart=:kickstart,
         name=:name,
         architecture=:architecture,
         kernel_options=:kernel_options,
         kickstart_metadata=:kickstart_metadata
         WHERE id=:id
         """

         ds = u.to_datastruct()
         self.db.cursor.execute(st, ds)
         self.db.connection.commit()
         self.sync( {} )

         return success(ds)


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

         st = """
         DELETE FROM distributions WHERE distributions.id=:id
         """

         self.db.cursor.execute(st, { "id" : u.id })
         self.db.connection.commit()

         return success()


    def list(self, token, dist_args):
         """
         Return a list of distributions.  The dist_args list is currently *NOT*
         used.  Ideally we need to include LIMIT information here for
         GUI pagination when we start worrying about hundreds of systems.
         """

         print "DEBUG: distribution list called"

         offset = 0
         limit  = 100
         if dist_args.has_key("offset"):
            offset = dist_args["offset"]
         if dist_args.has_key("limit"):
            limit = dist_args["limit"]

         st = """
         SELECT id,kernel,initrd,kickstart,name,architecture,kernel_options,kickstart_metadata
         FROM distributions LIMIT ?,?
         """ 

         results = self.db.cursor.execute(st, (offset,limit))
         results = self.db.cursor.fetchall()
         distributions = []

         for x in results:

             print "DEBUG: appending distribution item"

             data = {         
                "id"           : x[0],
                "kernel"       : x[1],
                "initrd"       : x[2],
                "kickstart"    : x[3],
                "name"         : x[4],
                "architecture" : x[5],
                "kernel_options" : x[6],
                "kickstart_metadata" : x[7]
             }
             distributions.append(DistributionData.produce(data).to_datastruct(True))

         print "DEBUG: returning distributions: %s" % distributions

         return success(distributions)


    def get(self, token, dist_args):
         """
         Return a specific distribution record.  Only the "id" is required in dist_args.
         """

         u = DistributionData.produce(dist_args,OP_GET) # force validation

         st = """
         SELECT id,kernel,initrd,kickstart,name,architecture,kernel_options,kickstart_metadata
         FROM distributions WHERE distributions.id=:id
         """

         self.db.cursor.execute(st,{ "id" : u.id })
         x = self.db.cursor.fetchone()
         if x is None:
             raise NoSuchObjectException(comment="distribution_get")

         data = {
                "id"                 : x[0],
                "kernel"             : x[1],
                "initrd"             : x[2],
                "kickstart"          : x[3],
                "name"               : x[4],
                "architecture"       : x[5],
                "kernel_options"     : x[6],
                "kickstart_metadata" : x[7]
         }

         return success(DistributionData.produce(data).to_datastruct(True))


methods = Distribution()
register_rpc = methods.register_rpc
