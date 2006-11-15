
class BaseObject(object):
 
   def load(self,hash,key,default=""):
      if hash.has_key(key):
          return hash[key]
      else:
          return default


