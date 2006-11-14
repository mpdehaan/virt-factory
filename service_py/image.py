from sqlalchemy import *

def make_table(creator, meta):
    return creator(Image, Table('images', meta,
        Column('id', Integer, primary_key=True),
        Column('name', String(255)),
        Column('version', String(255)),
        Column('filename', String(255)),
        Column('specfile', String(255)),
    ))

class Image(object):


   def to_datastruct(self):
      return {
         "id"          : self.id,
         "name"        : self.name,
         "version"     : self.version,
         "filename"    : self.filename,
         "specfile"    : self.specfile
      }

