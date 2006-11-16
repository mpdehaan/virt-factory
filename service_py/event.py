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

