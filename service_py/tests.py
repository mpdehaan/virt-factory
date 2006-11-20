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
import time

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
           (rc, token) =  self.api.user_login("admin","fedora")
           if rc != 0:
               self.fail("default user account missing: %s" % rc)
           self.TOKEN = token
           print "TOKEN = %s" % token

   def tearDown(self):
       pass

class LoginTests(BaseTest):
   # check for invalid user raising exception
   # check for 
   def test_valid_user(self):
      (rc, data) = self.api.user_login("admin", "fedora")
      self.failUnlessEqual(rc, 0, "can login")

   def test_invalid_user(self):
      (rc, data) = self.api.user_login("mrwizard","xyz")
      self.failUnlessEqual(rc, codes.ERR_USER_INVALID, "invalid user")

   def test_invalid_password(self):
      (rc, data) = self.api.user_login("admin","foosball")
      self.failUnlessEqual(rc, codes.ERR_PASSWORD_INVALID, "invalid pass")

   def test_method_access(self):
      (rc, data) = self.api.user_login("admin","foosball")
      (rc, data) = self.api.user_list(data) 
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
       (rc, users) = self.call(self.api.user_list)
       self.failUnlessEqual(rc, codes.ERR_SUCCESS, "return codes")
       self.failUnlessEqual(len(users),1,"only 1 user out of the box")

   sample_user = {
          "username"    : "test_add", 
          "password"    : "pw123456",
          "first"       : "first",
          "middle"      : "middle",
          "last"        : "last",
          "description" : "description",
          "email"       : "email"
   }
   
   def test_adds_that_will_pass(self):
       (rc1, data1) = self.call(self.api.user_add, self.sample_user)
       self.failUnlessEqual(rc1, 0, "user add ok")
       (rc2, data2) = self.call(self.api.user_list)
       self.failUnlessEqual(rc2, 0, "user list ok")
       self.failUnlessEqual(len(data2),2,"now there are two, two wugs")
       id = -1
       for user_obj in data2:
          if user_obj["username"] == "test_add":
              id = user_obj["id"]
       (rc3, data3) = self.call(self.api.user_get, { "id" : id })
       self.failUnlessEqual(rc3,0, "user get ok")
       self.failUnlessEqual(data3["username"],"test_add","retrieval")
       self.failUnlessEqual(id,data1,"function returned UID")

   def test_adds_that_will_fail(self):
       user = self.sample_user.copy()
       user["username"] = "admin"
       (rc1, data) = self.call(self.api.user_add, user)
       # FIXME: the following code does not fail and needs fixing in SW
       # self.failUnlessEqual(rc1, codes.ERR_INVALID_ARGUMENTS, "duplicate user")
       # FIXME: as more validation gets added, add more here
       # or rather, add them here now and fix the tests later

   def test_limit_query(self):
       user1 = self.sample_user.copy()
       user1["username"] = "u1"
       user2 = self.sample_user.copy()
       user2["username"] = "u2"
       user3 = self.sample_user.copy()
       user3["username"] = "u3"
       user4 = self.sample_user.copy()
       user4["username"] = "u4"

       # FIXME: this uncovers an interesting bug in that multiple ads per
       # second don't work.  This needs to be fixed (use SQL counters).
       (rc1, data1) = self.call(self.api.user_add, user1)
       time.sleep(2) # temporary: FIXME
       (rc2, data2) = self.call(self.api.user_add, user2)
       time.sleep(2) # temporary: FIXME
       (rc3, data3) = self.call(self.api.user_add, user3)
       time.sleep(2) # temporary: FIXME
       (rc4, data4) = self.call(self.api.user_add, user4)
       for (rc,data) in zip([rc1,rc2,rc3,rc4],[data1,data2,data3,data4]):
          self.failUnlessEqual(rc, 0, "addition ok: %s" % data)

       (rc5, d5) = self.call(self.api.user_list, { "offset" : 1, "limit" : 2 })
       self.failUnlessEqual(rc, 0, "limit query 1 ok")
       self.failUnlessEqual(len(d5), 2, "correct number of results")
       (rc6, d6) = self.call(self.api.user_list, { "offset" : 1, "limit" : 3 })
       self.failUnlessEqual(rc, 0, "limit query 2 ok")
       self.failUnlessEqual(len(d5), 3, "correct number of results")
       (rc7, d7) = self.call(self.api.user_list, {})
       self.failUnlessEqual(rc, 0, "standard query ok")
       self.failUnlessEqual(len(d7),5, "all results returned")  
 
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


