from sqlalchemy import *
import codes
import baseobj

def make_table(meta):
    tbl = Table('images', meta, autoload=True)
    mapper(Image,tbl)
    return tbl

class Image(baseobj.BaseObject):


   def to_datastruct(self):
      return {
         "id"          : self.id,
         "name"        : self.name,
         "version"     : self.version,
         "filename"    : self.filename,
         "specfile"    : self.specfile
      }

