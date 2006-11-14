from sqlalchemy import *


def make_table(creator, meta):
    return creator(Deployment, Table('deployments', meta,
         Column("id", Integer, primary_key=True),
         Column("machine_id", Integer),
         Column("image_id", Integer),
         Column("state", Integer)
    ))

class Deployment(object):

   def to_datastruct(self):
      return {
         "id"          : self.id,
         "machine_id"  : self.machine_id,
         "image_id"    : self.image_id,
         "state"       : self.state,
      }

