from sqlalchemy import *
import codes

def make_table(meta):
    tbl = Table('deployments', meta, autoload=True)
    return tbl

class Deployment(object):

   def to_datastruct(self):
      return {
         "id"          : self.id,
         "machine_id"  : self.machine_id,
         "image_id"    : self.image_id,
         "state"       : self.state,
      }

