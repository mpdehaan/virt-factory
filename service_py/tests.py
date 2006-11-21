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

   def custom_setup():
       pass

   def setUp(self):
       self.api = shadow.XmlRpcInterface()
       shadow.database_reset()
       self.custom_setup()
       if self.TOKEN is None:
           (rc, token) =  self.api.user_login("admin","fedora")
           if rc != 0:
               self.fail("default user account missing: %s" % rc)
           self.TOKEN = token

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
   
   def test_user_adds_that_will_pass(self):
       (rc1, data1) = self.call(self.api.user_add, self.sample_user)
       self.failUnlessEqual(rc1, 0, "user add ok")
       (rc2, data2) = self.call(self.api.user_list)
       self.failUnlessEqual(rc2, 0, "user list ok")
       self.failUnlessEqual(len(data2),2,"now there are two, two wugs")
       id = -1
       for user_obj in data2:
          if user_obj["username"] == "test_add":
              id = user_obj["id"]
       self.failUnlessEqual(data1, id, "returned UID not equal to found")
       (rc3, data3) = self.call(self.api.user_get, { "id" : id })
       self.failUnlessEqual(rc3,0, "user get ok")
       self.failUnlessEqual(data3["username"],"test_add","retrieval")
       self.failUnlessEqual(id,data1,"function returned UID")

   def test_user_adds_that_will_fail(self):
       user = self.sample_user.copy()
       user["username"] = "admin"
       (rc1, data) = self.call(self.api.user_add, user)
       # FIXME: the following code does not fail and needs fixing ...
       # second primary key?
       self.failUnlessEqual(rc1, codes.ERR_SQL, "duplicate user: %s, %s" % (rc1,data))
       # FIXME: as more validation gets added, add more here
       # or rather, add them here now and fix the tests later

   def test_user_limit_query(self):
       user1 = self.sample_user.copy()
       user1["username"] = "u1"
       user2 = self.sample_user.copy()
       user2["username"] = "u2"
       user3 = self.sample_user.copy()
       user3["username"] = "u3"
       user4 = self.sample_user.copy()
       user4["username"] = "u4"

       # FIXME: SQL adds need to catch errors, i.e. duplicate inserts
       (rc1, data1) = self.call(self.api.user_add, user1)
       (rc2, data2) = self.call(self.api.user_add, user2)
       (rc3, data3) = self.call(self.api.user_add, user3)
       (rc4, data4) = self.call(self.api.user_add, user4)
       for (rc,data) in zip([rc1,rc2,rc3,rc4],[data1,data2,data3,data4]):
          self.failUnlessEqual(rc, 0, "addition ok: %s" % data)

       (rc5, d5) = self.call(self.api.user_list, { "offset" : 1, "limit" : 2 })
       self.failUnlessEqual(rc, 0, "limit query 1 ok")
       self.failUnlessEqual(len(d5), 2, "correct number of results")
       (rc6, d6) = self.call(self.api.user_list, { "offset" : 1, "limit" : 3 })
       self.failUnlessEqual(rc, 0, "limit query 2 ok")
       self.failUnlessEqual(len(d6), 3, "correct number of results: %s" % len(d6))
       (rc7, d7) = self.call(self.api.user_list, {})
       self.failUnlessEqual(rc, 0, "standard query ok")
       self.failUnlessEqual(len(d7),5, "all results returned")  

   def test_user_edit(self):
       user1 = self.sample_user.copy()
       (rc1, id) = self.call(self.api.user_add, user1)
       self.failUnlessEqual(rc1,0,"add: %s" % rc1)
       user1["description"] = "blahblahblah"
       user1["id"] = id
       (rc2, data2) = self.call(self.api.user_edit, user1)
       self.failUnlessEqual(rc2,0,"edit: %s, %s" % (rc2, data2))
       (rc3, data3) = self.call(self.api.user_get, { "id" : id })
       self.failUnlessEqual(rc3,0,"get")
       self.failUnlessEqual(data3["description"],"blahblahblah","changed")
       self.failUnlessEqual(data3,user1,"totally correct 3")
       self.failUnlessEqual(data2,user1,"totally correct 2")

   def test_user_delete(self):
       (rc0, data0) = self.call(self.api.user_list)
       self.failUnlessEqual(rc0, 0, "list ok")
       user1 = self.sample_user.copy()
       (rc1, data1) = self.call(self.api.user_add, user1)
       self.failUnlessEqual(rc1, 0, "add ok")
       (rc2, data2) = self.call(self.api.user_list)
       self.failUnlessEqual(rc2, 0, "list ok")
       self.failUnlessEqual(len(data2)-len(data0),1,"working add")
       (rc3, data3) = self.call(self.api.user_get, { "id" : data1 })
       self.failUnlessEqual(rc3, 0, "working get: %s" % rc3)
       self.failUnlessEqual(type(data3),dict,"got a dict: %s" % type(data3))
       (rc4, data4) = self.call(self.api.user_delete, { "id" : data1 })
       self.failUnlessEqual(rc4, 0, "working delete")
       (rc5, data5) = self.call(self.api.user_list)
       self.failUnlessEqual(len(data5),len(data0),"back to initial size")
       (rc6, data6) = self.call(self.api.user_get, { "id" : data1 })
       self.failUnlessEqual(rc6, codes.ERR_NO_SUCH_OBJECT,"deleted: %s, %s" % (rc6,data6))
 
class BasicCRUDTests(BaseTest):
   # list
   # add (passing + cardinality)
   # add duplicate should fail
   # delete should pass
   # delete nonexisting should fail
   # edit (should pass)
   # edit shouldn't be allowed to change certain fields

   sample = {
          "name"        : "foo", 
          "version"     : "1.01",
          "filename"    : "/tmp/foo",
          "specfile"    : "/tmp/bar"
   }
   funcs = {
          "add_func"    : None
          "delete_func" : None
          "list_func"   : None
          "edit_func"   : None
          "get_func"    : None
   }
   name_field = "name"
   
   def test_image_adds_that_will_pass(self):
       (rc1, data1) = self.call(self.funcs["add_func"], self.sample)
       self.failUnlessEqual(rc1, 0, "add ok")
       (rc2, data2) = self.call(self.funcs["list_func"])
       self.failUnlessEqual(rc2, 0, "list ok")
       self.failUnlessEqual(len(data2),1,"successful add")
       id = -1
       for obj in data2:
          if obj[self.name_field] == "foo":
              id = obj["id"]
       self.failUnlessEqual(data1, id, "returned UID not equal to found")
       (rc3, data3) = self.call(self.api.image_get, { "id" : id })
       self.failUnlessEqual(rc3,0, "get ok")
       self.failUnlessEqual(data3[self.name_field],"foo","retrieval")
       self.failUnlessEqual(id,data1,"function returned UID")

   def test_image_adds_that_will_fail(self):
       user = self.sample.copy()
       user[self.name_field] = "foo"
       (rc1, data) = self.call(self.funcs["add_func"], user)
       self.failUnlessEqual(rc1, codes.ERR_SQL, "duplicate object: %s, %s" % (rc1,data))

   def test_image_limit_query(self):
       s1 = self.sample.copy()
       s1["name"] = "1"
       s2 = self.sample.copy()
       s2["name"] = "2"
       s3 = self.sample.copy()
       s3["name"] = "3"
       s4 = self.sample.copy()
       s4["name"] = "4"

       # FIXME: SQL adds need to catch errors, i.e. duplicate inserts
       (rc1, data1) = self.call(self.funcs["add_func"], s1)
       (rc2, data2) = self.call(self.funcs["add_func"], s2)
       (rc3, data3) = self.call(self.funcs["add_func"], s3)
       (rc4, data4) = self.call(self.funcs["add_func"], s4)
       for (rc,data) in zip([rc1,rc2,rc3,rc4],[data1,data2,data3,data4]):
          self.failUnlessEqual(rc, 0, "addition ok: %s" % data)

       (rc5, d5) = self.call(self.funcs["list_func"], { "offset" : 1, "limit" : 2 })
       self.failUnlessEqual(rc, 0, "limit query 1 ok")
       self.failUnlessEqual(len(d5), 2, "correct number of results")
       (rc6, d6) = self.call(self.funcs["list_func"], { "offset" : 1, "limit" : 3 })
       self.failUnlessEqual(rc, 0, "limit query 2 ok")
       self.failUnlessEqual(len(d6), 3, "correct number of results: %s" % len(d6))
       (rc7, d7) = self.call(self.funcs["list_func"], {})
       self.failUnlessEqual(rc, 0, "standard query ok")
       self.failUnlessEqual(len(d7),5, "all results returned")  

   def test_image_edit(self):
       s1 = self.sample.copy()
       (rc1, id) = self.call(self.funcs["add_func"], s1)
       self.failUnlessEqual(rc1,0,"add: %s" % rc1)
       user1[self.name_field] = "blahblahblah"
       user1["id"] = id
       (rc2, data2) = self.call(self.funcs["edit_func"], user1)
       self.failUnlessEqual(rc2,0,"edit: %s, %s" % (rc2, data2))
       (rc3, data3) = self.call(self.funcs["get_func"], { "id" : id })
       self.failUnlessEqual(rc3,0,"get")
       self.failUnlessEqual(data3[self.name_field],"blahblahblah","changed")
       self.failUnlessEqual(data3,user1,"modified 1")
       self.failUnlessEqual(data2,user1,"modified 2")

   def test_image_delete(self):
       # get # of records
       (rc0, data0) = self.call(self.funcs["list_func"])
       self.failUnlessEqual(rc0, 0, "list ok")
       s1 = self.sample.copy()
       (rc1, data1) = self.call(self.funcs["add_func"], s1)
       self.failUnlessEqual(rc1, 0, "add ok")
       (rc2, data2) = self.call(self.funcs["list_func"])
       self.failUnlessEqual(rc2, 0, "list ok")
       self.failUnlessEqual(len(data2)-len(data0),1,"working add")
       (rc3, data3) = self.call(self.funcs["get_func"], { "id" : data1 })
       self.failUnlessEqual(rc3, 0, "working get: %s" % rc3)
       self.failUnlessEqual(type(data3),dict,"got a dict: %s" % type(data3))
       (rc4, data4) = self.call(self.funcs["delete_func"], { "id" : data1 })
       self.failUnlessEqual(rc4, 0, "working delete")
       (rc5, data5) = self.call(self.funcs["list_func"])
       self.failUnlessEqual(len(data5),len(data0),"back to initial size")
       (rc6, data6) = self.call(self.funcs["get_func"], { "id" : data1 })
       self.failUnlessEqual(rc6, codes.ERR_NO_SUCH_OBJECT,"deleted: %s, %s" % (rc6,data6))

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


