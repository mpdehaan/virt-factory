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


class BaseObject(object):
 
   def load(self,hash,key,default=None):
      if hash.has_key(key):
          return hash[key]
      else:
          return default

   def to_datastruct(self):
      ds = self.to_datastruct_internal()
      ds = self.__ds_fixup(ds)
      return ds

   def __ds_fixup(self, x, forward=True):
       """
       Workaround for XMLRPC and allow_none
       map None to -1 for all return datastructures.
       """
       if type(x) == list:
           for i,j in enumerate(x):
               if j is None:
                  x[i] = -1
               elif type(j) == dict or type(j) == list:
                  self.ds_fixup(x)
       if type(x) == dict:
           for i,j in x.iteritems():
               if j is None:
                   x[i] = -1
               elif type(j) == dict or type(j) == list:
                   self.ds_fixup(x)
       return x

