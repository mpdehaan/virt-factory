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

   def to_datastruct(self,to_caller=False):
      ds = self.to_datastruct_internal()
      if to_caller:
          # don't send NULLs
          ds = self.remove_nulls(ds)
      return ds

   def remove_nulls(self, x, forward=True):
       """
       If any entries are None in the datastructure, prune them.
       XMLRPC can't marshall None
       """
       if type(x) == list:
           newx = []
           for i in x:
               if type(i) == list or type(i) == dict:
                   newx.append(self.__ds_fixup(i))
               elif i is not None:
                   newx.append(i)
           x = newx
       elif type(x) == dict:
           newx = {}
           for i,j in x.iteritems():
               if type(j) == list or type(j) == dict:
                   newx[i] = self.__ds_fixup(x)
               elif j is not None:
                   newx[i] = j
           x = newx
       return x

