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
import sys

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

   def custom_setup(self):
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

class BaseCrudTests(BaseTest):

   """ 
   Defines the GUTS of what is needed to test basic database and API
   functionality.  Join tables will get more interesting.
   """

   sample = {
          "name"        : "foo", 
          "version"     : "1.01",
          "filename"    : "/tmp/foo",
          "specfile"    : "/tmp/bar"
   }
   funcs = {
          "add_func"    : None,
          "delete_func" : None,
          "list_func"   : None,
          "edit_func"   : None,
          "get_func"    : None
   }
   name_field = "name"
   change_test_field = "name"
   initial_rows = 0 

   def _test_add(self):
       (rc0, data0) = self.call(self.funcs["list_func"])
       self.failUnlessEqual(rc0, 0, "list ok: %s" % rc0)
       (rc1, data1) = self.call(self.funcs["add_func"], self.sample)
       self.failUnlessEqual(rc1, 0, "add ok: %s" % rc1)
       (rc2, data2) = self.call(self.funcs["list_func"])
       self.failUnlessEqual(rc2, 0, "list ok")
       self.failUnlessEqual(len(data2),len(data0)+1,"successful add")
       id = -1
       for obj in data2:
          if obj[self.name_field] == self.sample[self.name_field]:
              id = obj["id"]
       self.failUnlessEqual(data1, id, "returned UID not equal to found: %s,%s" % (data1,id))
       (rc3, data3) = self.call(self.funcs["get_func"], { "id" : id })
       self.failUnlessEqual(rc3,0, "get ok")
       self.failUnlessEqual(data3[self.name_field], self.sample[self.name_field],"retrieval: %s, %s" % (data3[self.name_field], "foo"))
       self.failUnlessEqual(id,data1,"function returned UID")

       obj = self.sample.copy()
       obj[self.name_field] = "somethingsomething"
       (rc3, data3) = self.call(self.funcs["add_func"], obj)
       (rc4, data4) = self.call(self.funcs["add_func"], obj)
       self.failUnlessEqual(rc4, codes.ERR_SQL, "duplicate object: %s, %s" % (rc4,data4))

   def _test_list(self):
       s1 = self.sample.copy()
       s1[self.name_field] = "1"
       s2 = self.sample.copy()
       s2[self.name_field] = "2"
       s3 = self.sample.copy()
       s3[self.name_field] = "3"
       s4 = self.sample.copy()
       s4[self.name_field] = "4"

       (rc1, data1) = self.call(self.funcs["add_func"], s1)
       (rc2, data2) = self.call(self.funcs["add_func"], s2)
       (rc3, data3) = self.call(self.funcs["add_func"], s3)
       (rc4, data4) = self.call(self.funcs["add_func"], s4)
       for (rc,data) in zip([rc1,rc2,rc3,rc4],[data1,data2,data3,data4]):
          self.failUnlessEqual(rc, 0, "addition ok: %s, %s" % (rc,data))

       (rc5, d5) = self.call(self.funcs["list_func"], { "offset" : 1, "limit" : 2 })
       self.failUnlessEqual(rc, 0, "limit query 1 ok")
       self.failUnlessEqual(len(d5), 2, "correct number of results")
       (rc6, d6) = self.call(self.funcs["list_func"], { "offset" : 1, "limit" : 3 })
       self.failUnlessEqual(rc, 0, "limit query 2 ok")
       self.failUnlessEqual(len(d6), 3, "correct number of results: %s" % len(d6))
       (rc7, d7) = self.call(self.funcs["list_func"], {})
       self.failUnlessEqual(rc, 0, "standard query ok")
       self.failUnlessEqual(len(d7),4+self.initial_rows, "all results returned")  

   def _test_edit(self):
       s1 = self.sample.copy()
       (rc1, id) = self.call(self.funcs["add_func"], s1)
       self.failUnlessEqual(rc1,0,"add: %s" % rc1)
       s1[self.change_test_field] = "blahblahblah"
       s1["id"] = id
       (rc2, data2) = self.call(self.funcs["edit_func"], s1)
       self.failUnlessEqual(rc2,0,"edit: %s, %s" % (rc2, data2))
       (rc3, data3) = self.call(self.funcs["get_func"], { "id" : id })
       self.failUnlessEqual(rc3,0,"get")
       self.failUnlessEqual(data3[self.change_test_field],"blahblahblah","changed: %s" % (data3))
       self.failUnlessEqual(data3,s1,"modified 1: %s vs %s" % (data3,s1))
       self.failUnlessEqual(data2,s1,"modified 2: %s vs %s" % (data2,s1))

   def _test_delete(self):
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

class ImageTests(BaseCrudTests):

   def custom_setup(self):
      self.sample = {
         "name" : "foo",
         "version" : "1.01",
         "filename" : "/tmp/foo",
         "specfile" : "/tmp/bar",
         "distribution_id" : -1, 
         "virt_storage_size" : 500,
         "virt_ram" : 2048,
         "kickstart_metadata" : ""
      } 
      self.funcs = {
         "add_func"    : self.api.image_add,
         "edit_func"   : self.api.image_edit,
         "list_func"   : self.api.image_list, 
         "get_func"    : self.api.image_get,
         "delete_func" : self.api.image_delete
      }
      self.name_field = "name"
      self.change_test_field = "name"

   # FIXME: more tests of image specific validation

   def test_image_list(self):   self._test_list()
   def test_image_edit(self):   self._test_edit()
   def test_image_delete(self): self._test_delete()
   def test_image_add(self):    self._test_add()

class MachineTests(BaseCrudTests):

   def custom_setup(self):
      self.sample = {
         "address" : "foo",
         "architecture" : 1,
         "processor_speed" : 2200,
         "processor_count" : 2,
         "memory" : 1024,
         "distribution_id" : -1,
         "kernel_options" : "ksdevice=eth0 text",
         "kickstart_metadata" : "",
         "list_group" : "building three"
      } 
      self.funcs = {
         "add_func"    : self.api.machine_add,
         "edit_func"   : self.api.machine_edit,
         "list_func"   : self.api.machine_list, 
         "get_func"    : self.api.machine_get,
         "delete_func" : self.api.machine_delete
      }
      self.name_field = "address"
      self.change_test_field = "address"
      self.initial_rows = 0
   
   # FIXME: more tests of machine specific validation

   def test_machine_list(self):   self._test_list()
   def test_machine_edit(self):   self._test_edit()
   def test_machine_delete(self): self._test_delete()
   def test_machine_add(self):    self._test_add()

class DistributionTests(BaseCrudTests):

   def custom_setup(self):
      self.sample = {
         "kernel"    : "kernel",
         "initrd"    : "initrd",
         "options"   : "options",
         "kickstart" : "kickstart",
         "name"      : "name",
      }
      self.funcs = {
         "add_func"    : self.api.distribution_add,
         "edit_func"   : self.api.distribution_edit,
         "list_func"   : self.api.distribution_list,
         "get_func"    : self.api.distribution_get,
         "delete_func" : self.api.distribution_delete
      }
      self.name_field = "name"
      self.change_test_field = "options"
      self.initial_rows = 0

   # FIXME: more tests of distribution specific validation

   def test_distribution_list(self):   self._test_list()
   def test_distribution_edit(self):   self._test_edit()
   def test_distribution_delete(self): self._test_delete()
   def test_distribution_add(self):    self._test_add()

  

class UserTests(BaseCrudTests):
   def custom_setup(self):
      self.sample = {
          "username"    : "foo",
          "password"    : "pass", 
          "first"       : "F",
          "middle"      : "M",
          "last"        : "L",
          "description" : "...",
          "email"       : "testemail@redhat.com"
      } 
      self.funcs = {
          "add_func"    : self.api.user_add,
          "edit_func"   : self.api.user_edit,
          "list_func"   : self.api.user_list,
          "get_func"    : self.api.user_get,
          "delete_func" : self.api.user_delete
      }
      self.name_field = "username"
      self.change_test_field = "description"
      self.initial_rows = 1  
 
   def test_user_list(self):   self._test_list()
   def test_user_edit(self):   self._test_edit()
   def test_user_delete(self): self._test_delete()
   def test_user_add(self):    self._test_add()

   # FIXME: additional tests, such as "can't delete admin"
   # FIXME: validation that is user-centric
   # can't change username, etc

class DeploymentTests(BaseTest):
   # similar tests to user plus...
   # add: image and machine must preexist
   # edit: orphan detection also applies
   # list: verify that image and machine data are nested

   def test_delete(self):
       self.test_add_one()
       (rc0, data0) = self.call(self.api.deployment_list)
       self.failUnlessEqual(rc0, 0, "list ok")
       self.failUnlessEqual(len(data0),1,"cardinality")
       record = data0[0]
       id = record["id"]
       (rc1, data1) = self.call(self.api.deployment_delete, { "id" : id})
       self.failUnlessEqual(rc1, 0, "delete ok: %s, %s" % (rc1, data1))
       (rc2, data2) = self.call(self.api.deployment_list)
       self.failUnlessEqual(rc2, 0, "list ok")
       self.failUnlessEqual(type(data2), list, "list returned")
       self.failUnlessEqual(len(data2), 0, "empty list")

   def test_orphan_prevention(self):
       self.test_add_one()
       (rc0, data0) = self.call(self.api.deployment_list)
       obj = data0[0]
       (rc1, data1) = self.call(self.api.image_delete, { "id" : obj["image_id"] })
       self.failUnlessEqual(rc1, codes.ERR_ORPHANED_OBJECT)
       (rc2, data2) = self.call(self.api.image_get, { "id" : obj["image_id"] })
       self.failUnlessEqual(rc2, 0, "image get ok")
       self.failUnlessEqual(data2, obj["image"], "image unchanged")
       (rc3, data3) = self.call(self.api.machine_delete, { "id" : obj["machine_id"] })
       self.failUnlessEqual(rc3, codes.ERR_ORPHANED_OBJECT)
       (rc4, data4) = self.call(self.api.machine_get, { "id" : obj["machine_id"] })
       self.failUnlessEqual(rc4, 0, "machine get ok")
       self.failUnlessEqual(data4, obj["machine"], "machine unchanged") 

   def test_edit(self):
       self.test_add_one()
       (rc0, data0) = self.call(self.api.deployment_list)
       self.failUnlessEqual(rc0, 0, "list ok")
       obj = data0[0]
       obj["state"] = 12345678
       (rc1, data1) = self.call(self.api.deployment_edit, obj)
       self.failUnlessEqual(rc1, 0, "edit ok")
       (rc2, data2) = self.call(self.api.deployment_get, { "id" : obj["id"] })
       self.failUnlessEqual(rc2, 0, "get ok")
       self.failUnlessEqual(data2, obj, "edited as expected")
       # now check to make sure integrity is preserved across join
       # machines and images
       machine_id = obj["machine_id"]
       image_id = obj["image_id"]
       obj["machine_id"] = -1
       (rc3, data3) = self.call(self.api.deployment_edit, obj)
       self.failUnlessEqual(rc3, codes.ERR_INVALID_ARGUMENTS, "edit fail: %s" % rc3)
       self.failUnlessEqual(data3, "machine_id", "listed the arg")
       obj["machine_id"] = machine_id
       obj["image_id"] = -2 
       (rc4, data4) = self.call(self.api.deployment_edit, obj)
       self.failUnlessEqual(rc4, codes.ERR_INVALID_ARGUMENTS, "invalid id")
       self.failUnlessEqual(data4, "image_id", "listed the arg: %s" % data3)
       (rc5, data5) = self.call(self.api.deployment_get, { "id" : obj["id"]})
       obj["image_id"] = image_id
       self.failUnlessEqual(obj["image"], data5["image"], "no changes made")
       self.failUnlessEqual(obj["machine"], data5["machine"], "no changes made")

   def test_add_with_orphans(self):
       dep2 = {
           "state" : 27,
           "image_id" : 8675309,
           "machine_id" : 8675309
       }
       (rc0, data0) = self.call(self.api.deployment_add, dep2)
       self.failUnlessEqual(rc0, codes.ERR_ORPHANED_OBJECT, "orphans")


   def test_add_one(self):
       sample_image = {
           "name"     : "dep_image",
           "version"  : "5150.812",
           "filename" : "/dev/null", 
           "specfile" : "/dev/true",
           "distribution_id" : -1,
           "virt_storage_size" : 456,
           "virt_ram" : 789,
           "kickstart_metadata" : "foo=bar baz=foo 12345"
       }
       sample_machine = {
           "address"         : "foo.example.com",
           "architecture"    : 1,
           "processor_speed" : 3000,
           "processor_count" : 1,
           "memory"          : 4096,
           "distribution_id" : -1,
           "kernel_options"  : "foo=bar 12345",
           "kickstart_metadata" : "bar=foo baz=foo foo=bar",
           "list_group"      : "server room 5"
       }
       sample_deployment = {
           "machine_id"      : None,
           "image_id"        : None,
           "state"           : 0
       }
       (rc0, data0) = self.call(self.api.image_add, sample_image)
       self.failUnlessEqual(rc0, 0, "image add")
       (rc1, data1) = self.call(self.api.machine_add, sample_machine)
       self.failUnlessEqual(rc0, 0, "machine add")
       dep = sample_deployment.copy()
       dep["machine_id"] = data1 
       dep["image_id"] = data0
       sample_image["id"] = data0
       sample_machine["id"] = data1
       (rc2, data2) = self.call(self.api.deployment_add, dep)
       self.failUnlessEqual(rc2, 0, "deployment add: %s, %s" % (rc2, data2))
       (rc3, data3) = self.call(self.api.deployment_list)
       self.failUnlessEqual(rc3, 0, "deployment list")
       self.failUnlessEqual(len(data3), 1, "one machine")
       self.failUnlessEqual(type(data3), list, "returns a list")
       # test nested data in "list"
       self.failUnlessEqual(type(data3[0]), dict, "first element is a dict")
       self.failUnlessEqual(data3[0].has_key("machine"), True, "machine filled out")
       self.failUnlessEqual(type(data3[0]["machine"]), dict, "machine is a dict")
       self.failUnlessEqual(cmp(data3[0]["machine"],sample_machine),0,"machine equal: \n%s\n%s" % (data3[0]["machine"], sample_machine))
       self.failUnlessEqual(data3[0].has_key("image"), True, "image filled out")
       self.failUnlessEqual(type(data3[0]["image"]), dict, "image is a dict")
       self.failUnlessEqual(cmp(data3[0]["image"],sample_image),0,"image equal")
       # test nested data in "get"
       (rc4, data4) = self.call(self.api.deployment_get, {"id" : data2})
       self.failUnlessEqual(cmp(data4["machine"], sample_machine), 0, "machine equal")
       self.failUnlessEqual(cmp(data4["image"], sample_image), 0, "image equal")
       
       # FIXME: test limit queries
       # FIXME: test edits



# others TBA

if __name__ == "__main__":
    unittest.main() 
    shadow.database_reset() # make it usable again


