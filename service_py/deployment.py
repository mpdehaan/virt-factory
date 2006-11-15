from sqlalchemy import *
import codes
import baseobj

def make_table(meta):
    tbl = Table('deployments', meta, autoload=True)
    return tbl

class Deployment(baseobj.BaseObject):

   def to_datastruct(self):
      return {
         "id"          : self.id,
         "machine_id"  : self.machine_id,
         "image_id"    : self.image_id,
         "state"       : self.state,
      }

