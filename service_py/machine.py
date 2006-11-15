from sqlalchemy import *
import codes
import baseobj

def make_table(meta):
    tbl = Table('machines', meta, autoload=True)
    mapper(Machine, tbl)
    return tbl

class Machine(object):

   def to_datastruct(self):
      return {
         "id"           : self.id,
         "architecture" : self.architecture,
         "processors"   : self.processors,
         "memory"       : self.memory
      }

