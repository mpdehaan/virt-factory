from sqlalchemy import *

class Audit(object):

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

def make_table(creator,meta):
   return creator(Audit, Table("audits", meta,
       Column('id', Integer, primary_key=True),
       Column('time', Integer),
       Column('machine_id', Integer),
       Column('deployment_id', Integer),
       Column('image_id', Integer),
       Column('severity', Integer),
       Column('category', VARCHAR(255)),
       Column('action', VARCHAR(255)),
       Column('comment', VARCHAR(255))
   ))

