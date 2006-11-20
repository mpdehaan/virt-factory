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

import shadow
import codes
import unittest
import traceback


class BaseTest(unittest.TestCase):

   TOKEN = None

   def call(self, function, *args):
       try: 
           return function(self.TOKEN, *args)
       except Exception, e:
           tb = traceback.format_exc()
           self.fail("raised exception\n%s" % tb)           

   def call_expect(self, exc_class, function,*args):
       call_this = lambda: self.call(function,args)
       failUnlessRaises(exc_class, call_this)

   def setUp(self):
       self.api = shadow.XmlRpcInterface()
       shadow.database_reset()
       if self.TOKEN is None:
           (sucess, rc, token) =  self.api.user_login("admin","fedora")
           self.TOKEN = token
           print "TOKEN = %s" % token

   def tearDown(self):
       pass

class LoginTests(BaseTest):
   # check for invalid user raising exception
   # check for 
   def test_valid_user(self):
      (success, rc, data) = self.api.user_login("admin", "fedora")
      self.failUnlessEqual(success,True,"can login")
      self.failUnlessEqual(rc, 0, "can login")

   def test_invalid_user(self):
      (success, rc, data) = self.api.user_login("mrwizard","xyz")
      self.failUnlessEqual(success,False,"can't login")
      self.failUnlessEqual(rc, codes.ERR_USER_INVALID, "invalid user")

   def test_invalid_password(self):
      (success, rc, data) = self.api.user_login("admin","foosball")
      self.failUnlessEqual(success,False,"can't login")
      self.failUnlessEqual(rc, codes.ERR_PASSWORD_INVALID, "invalid pass")

   def test_method_access(self):
      (success, rc, data) = self.api.user_login("admin","foosball")
      (success, rc, data) = self.api.user_list(data) 
      self.failUnlessEqual(success,False,"can't execute")
      self.failUnlessEqual(rc,codes.ERR_TOKEN_INVALID,"invalid token")


class UserTests(BaseTest):
   # list
   # add (passing + cardinality)
   # add duplicate should fail
   # delete should pass
   # delete of "admin" should fail
   # delete nonexisting should fail
   # edit (should pass)
   # edit shouldn't be allowed to change certain fields

   def test_list_default_user(self):
       (success, rc, users) = self.call(self.api.user_list)
       print "return: (%s, %s, %s)" % (success,rc,users)
       self.failUnlessEqual(success, True, "truthiness")
       self.failUnlessEqual(rc, codes.ERR_SUCCESS, "return codes")
       self.failUnlessEqual(len(users),1,"only 1 user out of the box")

   def test_add(self):
       pass

   def test_limit_query(self):
       pass
   
class ImageTests(BaseTest):
   # similar tests to user plus ...
   # can't delete an image if deployed
   pass

class MachineTests(BaseTest):
   # similar tests to machine plus ...
   # can't delete an image if used for a deployment
   pass

class DeploymentTests(BaseTest):
   # similar tests to user plus...
   # add: image and machine must preexist
   # edit: orphan detection also applies
   # list: verify that image and machine data are nested
   pass

# others TBA

if __name__ == "__main__":
    unittest.main() 


