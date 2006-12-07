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

   def call(self, function, *fn_args):
       try:
           return function(self.TOKEN, *fn_args)
       except Exception, e:
           tb = traceback.format_exc()
           self.fail("raised exception\n%s" % tb)           

   def custom_setup(self):
       pass

   def setUp(self):
       self.api = shadow.XmlRpcInterface()
       shadow.database_reset()
       self.custom_setup()
       try:
           self.TOKEN
       except:
           (rc, raw_results) = self.api.user_login("admin","fedora")
           if rc != 0:
               self.fail("default user account missing: %s" % rc)
           self.TOKEN = raw_results["data"]

   def tearDown(self):
       pass

class LoginTests(BaseTest):
   # check for invalid user raising exception
   # check for 
   def test_valid_user(self):
      (rc, raw_data) = self.api.user_login("admin", "fedora")
      self.failUnlessEqual(rc, 0, "can login")

   def test_invalid_user(self):
      (rc, raw_data) = self.api.user_login("mrwizard","xyz")
      self.failUnlessEqual(rc, codes.ERR_USER_INVALID, "invalid user")

   def test_invalid_password(self):
      (rc, raw_data) = self.api.user_login("admin","foosball")
      self.failUnlessEqual(rc, codes.ERR_PASSWORD_INVALID, "invalid pass")

   def test_method_access(self):
      (rc, raw_token) = self.api.user_login("admin","foosball")
      # FIXME
      # token = raw_token["data"]
      # (rc, raw_data) = self.api.user_list(token,{}) 
      # self.failUnlessEqual(rc,codes.ERR_TOKEN_INVALID,"invalid token")

class BaseCrudTests(BaseTest):

   """ 
   Defines the GUTS of what is needed to test basic database and API
   functionality.  Join tables will get more interesting.
   """

   sample = {
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
       (rc0, raw_data0) = self.call(self.funcs["list_func"],{})
       self.failUnlessEqual(rc0, 0, "list ok: %s" % rc0)
       data0 = raw_data0["data"]
       (rc1, raw_data1) = self.call(self.funcs["add_func"], self.sample)
       self.failUnlessEqual(rc1, 0, "add ok: %s" % rc1)
       data1 = raw_data1["data"]
       (rc2, raw_data2) = self.call(self.funcs["list_func"],{})
       self.failUnlessEqual(rc2, 0, "list ok")
       data2 = raw_data2["data"]
       self.failUnlessEqual(type(data2),list,"is a list: %s" % type(data2))
       self.failUnlessEqual(len(data2),len(data0)+1,"successful add")
       id = None
       for obj in data2:
          if obj[self.name_field] == self.sample[self.name_field]:
              id = obj["id"]
       self.failUnlessEqual(data1, id, "returned UID not equal to found: %s,%s" % (data1,id))
       (rc3, raw_data3) = self.call(self.funcs["get_func"], { "id" : id })
       self.failUnlessEqual(rc3,0, "get ok")
       data3 = raw_data3["data"]
       self.failUnlessEqual(data3[self.name_field], self.sample[self.name_field],"retrieval: %s, %s" % (data3[self.name_field], "foo"))
       self.failUnlessEqual(id,data1,"function returned UID")

       obj = self.sample.copy()
       obj[self.name_field] = "somethingsomething"
       (rc3, raw_data3) = self.call(self.funcs["add_func"], obj)
       self.failUnlessEqual(rc3, 0, "add")
       data3 = raw_data3["data"]
       (rc4, raw_data4) = self.call(self.funcs["add_func"], obj)
       self.failUnlessEqual(rc4, codes.ERR_SQL, "duplicate object: %s, %s" % (rc4, raw_data4))

   def _test_list(self):
       s1 = self.sample.copy()
       s1[self.name_field] = "1"
       s2 = self.sample.copy()
       s2[self.name_field] = "2"
       s3 = self.sample.copy()
       s3[self.name_field] = "3"
       s4 = self.sample.copy()
       s4[self.name_field] = "4"

       (rc1, raw_data1) = self.call(self.funcs["add_func"], s1)
       (rc2, raw_data2) = self.call(self.funcs["add_func"], s2)
       (rc3, raw_data3) = self.call(self.funcs["add_func"], s3)
       (rc4, raw_data4) = self.call(self.funcs["add_func"], s4)
       self.failUnlessEqual(rc1, 0, "addition ok")
       self.failUnlessEqual(rc2, 0, "addition ok")
       self.failUnlessEqual(rc3, 0, "addition ok")
       self.failUnlessEqual(rc4, 0, "addition ok")

       (rc5, raw_d5) = self.call(self.funcs["list_func"], { "offset" : 1, "limit" : 2 })
       self.failUnlessEqual(rc5, 0, "limit query 1 ok")
       d5 = raw_d5["data"]
       self.failUnlessEqual(type(d5),list,"result is a list")
       self.failUnlessEqual(len(d5), 2, "correct number of results")
       (rc6, raw_d6) = self.call(self.funcs["list_func"], { "offset" : 1, "limit" : 3 })
       self.failUnlessEqual(rc6, 0, "limit query 2 ok")
       d6 = raw_d6["data"]
       self.failUnlessEqual(len(d6), 3, "correct number of results: %s" % len(d6))
       (rc7, raw_d7) = self.call(self.funcs["list_func"], {})
       self.failUnlessEqual(rc7, 0, "standard query ok")
       d7 = raw_d7["data"]
       self.failUnlessEqual(len(d7),4+self.initial_rows, "all results returned")  

   def _test_edit(self):
       s1 = self.sample.copy()
       (rc1, raw_id) = self.call(self.funcs["add_func"], s1)
       self.failUnlessEqual(rc1,0,"add: %s" % rc1)
       id = raw_id["data"]
       s1[self.change_test_field] = "blahblahblah"
       s1["id"] = id
       (rc2, raw_data2) = self.call(self.funcs["edit_func"], s1)
       self.failUnlessEqual(rc2,0,"edit: %s, %s" % (rc2, raw_data2))
       data2 = raw_data2["data"]
       (rc3, raw_data3) = self.call(self.funcs["get_func"], { "id" : id })
       self.failUnlessEqual(rc3,0,"get")
       data3 = raw_data3["data"]
       self.failUnlessEqual(data3[self.change_test_field],"blahblahblah","changed: %s" % (data3))
       # test all fields that aren't allowed to be NULL to determine
       # they were correctly modified (or preserved, as the case may be)
       for k in self.sample:
          v = self.sample[k]
          if v is not None:
              self.failUnlessEqual(data3[k],s1[k],"modified 1: %s vs %s" % (data3,s1))
              self.failUnlessEqual(data2[k],s1[k],"modified 2: %s vs %s" % (data2,s1))

   def _test_delete(self):
       (rc0, raw_data0) = self.call(self.funcs["list_func"], {})
       self.failUnlessEqual(rc0, 0, "list ok")
       data0 = raw_data0["data"]
       s1 = self.sample.copy()
       (rc1, raw_data1) = self.call(self.funcs["add_func"], s1)
       self.failUnlessEqual(rc1, 0, "add ok")
       data1 = raw_data1["data"]
       (rc2, raw_data2) = self.call(self.funcs["list_func"])
       self.failUnlessEqual(rc2, 0, "list ok")
       data2 = raw_data2["data"]
       self.failUnlessEqual(len(data2)-len(data0),1,"working add")
       (rc3, raw_data3) = self.call(self.funcs["get_func"], { "id" : data1 })
       self.failUnlessEqual(rc3, 0, "working get: %s" % rc3)
       data3 = raw_data3["data"]
       self.failUnlessEqual(type(data3),dict,"got a dict: %s" % type(data3))
       (rc4, raw_data4) = self.call(self.funcs["delete_func"], { "id" : data1 })
       self.failUnlessEqual(rc4, 0, "working delete")
       (rc5, raw_data5) = self.call(self.funcs["list_func"], {})
       self.failUnlessEqual(rc5, 0, "list ok")
       data5 = raw_data5["data"]
       self.failUnlessEqual(len(data5),len(data0),"back to initial size")
       (rc6, raw_data6) = self.call(self.funcs["get_func"], { "id" : data1 })
       self.failUnlessEqual(rc6, codes.ERR_NO_SUCH_OBJECT,"deleted: %s, %s" % (rc6,raw_data6))

class ImageTests(BaseCrudTests):

   def custom_setup(self):
      self.sample = {
         "name" : "foo",
         "version" : "1.01",
         "filename" : "/tmp/foo",
         "specfile" : "/tmp/bar",
         "distribution_id" : None, 
         "virt_storage_size" : 500,
         "virt_ram" : 2048,
         "kickstart_metadata" : "???",
         "kernel_options" : "????",
         "valid_targets" : 0,
         "is_container" : 0
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

   # FIXME: machine tests should be augmented to deal with nested
   # image info

   def custom_setup(self):
      self.sample = {
         "address" : "foo",
         "architecture" : 1,
         "processor_speed" : 2200,
         "processor_count" : 2,
         "memory" : 1024,
         "kernel_options" : "ksdevice=eth0 text",
         "kickstart_metadata" : "",
         "list_group" : "building three",
         "mac_address" : "AA:BB:CC:DD:EE:FF",
         "is_container" : 0,
         "image_id" : None
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
         "kernel"       : "kernel",
         "initrd"       : "initrd",
         "kickstart"    : "kickstart",
         "name"         : "name",
         "architecture" : 1,
         "kernel_options" : "?",
         "kickstart_metadata" : "??"
      }
      self.funcs = {
         "add_func"    : self.api.distribution_add,
         "edit_func"   : self.api.distribution_edit,
         "list_func"   : self.api.distribution_list,
         "get_func"    : self.api.distribution_get,
         "delete_func" : self.api.distribution_delete
      }
      self.name_field = "name"
      self.change_test_field = "kernel_options"
      self.initial_rows = 0

   # FIXME: more tests of distribution specific validation

   def test_distribution_list(self):   self._test_list()
   def test_distribution_edit(self):   self._test_edit()
   def test_distribution_delete(self): self._test_delete()
   def test_distribution_add(self):    self._test_add()

   def test_distribution_with_links(self):
       distro = self.sample.copy()
       machine = {
          "address" : "foo",
          "architecture" : 1,
          "processor_speed" : 2200,
          "processor_count" : 2,
          "memory" : 1024,
          "kernel_options" : "ksdevice=eth0 text",
          "kickstart_metadata" : "",
          "list_group" : "building three",
          "mac_address" : "FF:FF:FF:FF:FF:FF",
          "is_container" : 0,
          "image_id" : None
       }
       image = { 
          "name" : "foo",
          "version" : "1.01",
          "filename" : "/tmp/foo",
          "specfile" : "/tmp/bar",
          "distribution_id" : None,
          "virt_storage_size" : 500,
          "virt_ram" : 2048,
          "kickstart_metadata" : "@@",
          "kernel_options" : "@@@",
          "valid_targets" : 0,
          "is_container" : 0
       }
       (rc0, raw_data0) = self.call(self.api.image_add, image)
       self.failUnlessEqual(rc0, 0, "image_add")
       data0 = raw_data0["data"]
       (rc0a, raw_data0a) = self.call(self.api.image_get, { "id" : data0 })
       self.failUnlessEqual(rc0a, 0, "image_get")
       data0a = raw_data0a["data"]
 
       machine["image_id"] = data0
       (rc1, raw_data1) = self.call(self.api.machine_add, machine)
       data1 = raw_data1["data"]
       self.failUnlessEqual(rc1, 0, "machine_add")
       (rc1a, raw_data1a) = self.call(self.api.machine_get, { "id" : data1 })
       data1a = raw_data1a["data"] 
       self.failUnlessEqual(rc1a, 0, "machine_get")
       self.failUnlessEqual(data1a["image"], data0a, "machine contains nested image: %s, %s" % (data1a["image"],data0a))       

       # FIXME: rewrite this part, should be "machine contains nested distribution"
       # though the above code sets distribution_id to None, which is wrong.

       # 
       #image["image_id"] = data0
       #(rc2, raw_data2) = self.call(self.api.image_add, image)
       #data2 = raw_data2["data"]
       #self.failUnlessEqual(rc2, 0, "image_add")
       #(rc2b, raw_data2b) = self.call(self.api.image_list, {})
       #data2b = raw_data2b["data"]
       #self.failUnlessEqual(rc2b, 0, "image list ok")
       #self.failUnlessEqual(len(data2b), 1, "correct number of images returned")
       #(rc2a, raw_data2a) = self.call(self.api.image_get, { "id" : data2 })
       #data2a = raw_data2a["data"]
       #self.failUnlessEqual(rc2a, 0, "image_get: %s, %s" % (rc2a, data2a))
       #self.failUnlessEqual(data2a["image"], data0a, "image contains nested distribution")
       # 
       #(rc3, raw_data3) = self.call(self.api.distribution_delete, { "id" : data0 })
       #data3 = raw_data3["data"]
       #self.failUnlessEqual(rc3, codes.ERR_ORPHANED_OBJECT, "cannot delete distribution if in use")
 

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
       (rc1, raw_data1) = self.call(self.api.deployment_delete, { "id" : id})
       data1 = raw_data1["data"]
       self.failUnlessEqual(rc1, 0, "delete ok: %s, %s" % (rc1, data1))
       (rc2, raw_data2) = self.call(self.api.deployment_list)
       data2 = raw_data2["data"]
       self.failUnlessEqual(rc2, 0, "list ok")
       self.failUnlessEqual(type(data2), list, "list returned")
       self.failUnlessEqual(len(data2), 0, "empty list")

   def test_orphan_prevention(self):
       self.test_add_one()
       (rc0, raw_data0) = self.call(self.api.deployment_list)
       data0 = raw_data0["data"]
       obj = data0[0]
       (rc1, raw_data1) = self.call(self.api.image_delete, { "id" : obj["image_id"] })
       data1 = raw_data1["data"]
       self.failUnlessEqual(rc1, codes.ERR_ORPHANED_OBJECT)
       (rc2, raw_data2) = self.call(self.api.image_get, { "id" : obj["image_id"] })
       data2 = raw_data2["data"]
       self.failUnlessEqual(rc2, 0, "image get ok")
       self.failUnlessEqual(data2, obj["image"], "image unchanged")
       (rc3, raw_data3) = self.call(self.api.machine_delete, { "id" : obj["machine_id"] })
       data3 = raw_data3["data"]
       self.failUnlessEqual(rc3, codes.ERR_ORPHANED_OBJECT)
       (rc4, raw_data4) = self.call(self.api.machine_get, { "id" : obj["machine_id"] })
       data4 = raw_data4["data"]
       self.failUnlessEqual(rc4, 0, "machine get ok")
       self.failUnlessEqual(data4, obj["machine"], "machine unchanged") 

   def test_edit(self):
       self.test_add_one()
       (rc0, raw_data0) = self.call(self.api.deployment_list)
       data0 = raw_data0["data"]
       self.failUnlessEqual(rc0, 0, "list ok")
       obj = data0[0]
       obj["state"] = 12345678
       (rc1, raw_data1) = self.call(self.api.deployment_edit, obj)
       data1 = raw_data1["data"]
       self.failUnlessEqual(rc1, 0, "edit ok")
       (rc2, raw_data2) = self.call(self.api.deployment_get, { "id" : obj["id"] })
       data2 = raw_data2["data"]
       self.failUnlessEqual(rc2, 0, "get ok")
       self.failUnlessEqual(data2, obj, "edited as expected")
       # now check to make sure integrity is preserved across join
       # machines and images
       machine_id = obj["machine_id"]
       image_id = obj["image_id"]
       obj["machine_id"] = None
       (rc3, raw_data3) = self.call(self.api.deployment_edit, obj)
       data3 = raw_data3["data"]
       self.failUnlessEqual(rc3, codes.ERR_INVALID_ARGUMENTS, "edit fail: %s" % rc3)
       self.failUnlessEqual(data3, "machine_id", "listed the arg")
       obj["machine_id"] = machine_id
       obj["image_id"] = -2 
       (rc4, raw_data4) = self.call(self.api.deployment_edit, obj)
       data4 = raw_data4["data"]
       self.failUnlessEqual(rc4, codes.ERR_INVALID_ARGUMENTS, "invalid id")
       self.failUnlessEqual(data4, "image_id", "listed the arg: %s" % data3)
       (rc5, raw_data5) = self.call(self.api.deployment_get, { "id" : obj["id"]})
       data5 = raw_data5["data"]
       obj["image_id"] = image_id
       self.failUnlessEqual(obj["image"], data5["image"], "no changes made")
       self.failUnlessEqual(obj["machine"], data5["machine"], "no changes made")

   def test_add_with_orphans(self):
       dep2 = {
           "state" : 27,
           "image_id" : 8675309,
           "machine_id" : 8675309
       }
       (rc0, raw_data0) = self.call(self.api.deployment_add, dep2)
       self.failUnlessEqual(rc0, codes.ERR_ORPHANED_OBJECT, "orphans")


   def test_add_one(self):
       sample_image = {
           "name"               : "dep_image",
           "version"            : "5150.812",
           "filename"           : "/dev/null", 
           "specfile"           : "/dev/true",
           "virt_storage_size"  : 456,
           "virt_ram"           : 789,
           "kickstart_metadata" : "foo=bar baz=foo 12345",
           "kernel_options"     : "-----",
           "valid_targets"      : 0,
           "is_container"       : 0,
           "distribution_id"    : None
       }
       sample_machine = {
           "address"            : "foo.example.com",
           "architecture"       : 1,
           "processor_speed"    : 3000,
           "processor_count"    : 1,
           "memory"             : 4096,
           "kernel_options"     : "foo=bar 12345",
           "kickstart_metadata" : "bar=foo baz=foo foo=bar",
           "list_group"         : "server room 5",
           "mac_address"        : "BB:EE:EE:EE:FF",
           "is_container"       : 0,
           "image_id"           : None
       }
       sample_deployment = {
           "machine_id"         : None,
           "image_id"           : None,
           "state"              : 0
       }

       # add the image
       (rc0, raw_data0) = self.call(self.api.image_add, sample_image)
       self.failUnlessEqual(rc0, 0, "image add: %s, %s" % (rc0, raw_data0))
       data0 = raw_data0["data"]

       # add the machine
       (rc1, raw_data1) = self.call(self.api.machine_add, sample_machine)
       self.failUnlessEqual(rc1, 0, "machine add: %s, %s" % (rc1, raw_data1))
       data1 = raw_data1["data"]
       
       # add the deployment
       dep = sample_deployment.copy()
       dep["machine_id"] = data1 
       dep["image_id"] = data0
       sample_image["id"] = data0
       sample_machine["id"] = data1
       (rc2, raw_data2) = self.call(self.api.deployment_add, dep)
       self.failUnlessEqual(rc2, 0, "deployment add: %s, %s" % (rc2, raw_data2))
       data2 = raw_data2["data"]
      
       # check that the deployment contains a machine and an image
       (rc3, raw_data3) = self.call(self.api.deployment_list)
       data3 = raw_data3["data"]
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
       (rc4, raw_data4) = self.call(self.api.deployment_get, {"id" : data2})
       data4 = raw_data4["data"]
       self.failUnlessEqual(rc4, 0, "successful get: %s, %s" % (rc4,data4))
       self.failUnlessEqual(cmp(data4["machine"], sample_machine), 0, "machine equal")
       self.failUnlessEqual(cmp(data4["image"], sample_image), 0, "image equal")

       # FIXME: test limit queries
       # FIXME: test edits

class ConfigTests(BaseTest):

  def test_config_list(self):
       (rc0, raw_data0) = self.call(self.api.config_list, {})
       data0 = raw_data0["data"]
       self.failUnlessEqual(rc0, 0, "config_list ok: %s" % rc0)
       self.failUnlessEqual(type(data0), dict, "dict returned")

class AdvancedCobblerTests(BaseTest):

   def test_sync(self):
       # cobbler sync is normally invoked when adding a new machine or image.  this test verifies that it is working
       # by looking at cobbler's config and so forth.
       pass

if __name__ == "__main__":
    print "*********************************************************"
    print "*********************************************************"
    print "*********************************************************"
    print "*********************************************************"
    print "*********************************************************"
    print "*********************************************************"
    unittest.main() 
    shadow.database_reset() # make it usable again



