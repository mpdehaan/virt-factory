from sqlalchemy import *
import baseobj

class Audit(baseobj.BaseObject):

   def to_datastruct(self):
       return {
           "id"            : self.id,
           "time"          : self.time,
           "machine_id"    : self.machine_id,
           "deployment_id" : self.deployment_id,
           "image_id"      : self.image_id,
           "severity"      : self.severity,
           "category"      : self.category,
           "action"        : self.action,
           "comment"       : self.comment
       }

def make_table(meta):
   tbl = Table("events", meta, autoload=True)
   mapper(Audit,tbl)
   return tbl

