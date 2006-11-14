from sqlalchemy import *


def make_table(creator, meta):
    return creator(Machine, Table('machine', meta,
         Column("id", Integer, primary_key=True),
         Column("architecture", String(255)),
         Column("processors", String(255)),
         Column("memory", String(255))
    ))

class Machine(object):

   def to_datastruct(self):
      return {
         "id"           : self.id,
         "architecture" : self.architecture,
         "processors"   : self.processors,
         "memory"       : self.memory
      }

