"""
ShadowManager backend code.

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Scott Seago <sseago@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""


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

