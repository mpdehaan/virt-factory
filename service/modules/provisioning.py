#!/usr/bin/python
## Virt-factory backend code.
##
## Copyright 2006, Red Hat, Inc
## Michael DeHaan <mdehaan@redhat.com>
## Scott Seago <sseago@redhat.com>
## Adrian Likins <alikins@redhat.com>
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
##

# note:  this contains helper code for working with cobbler.  methods here
# should not be surfaced in the external API, but should be methods on 
# things like profile and deployments, etc.

# further note:  this class assumes validation has _already_ been
# done by various layers in the DB.  It will map DB constants
# to cobbler values, but it will not account for things like
# an invalid entry for a kernel filename, for instance.  In the event
# of something like that, exceptions will not be caught and will
# result (ultimately) in tracebacks to the caller.  This is by design
# as we don't want to cover up the source of what's going on from
# cobbler land...  MORAL: put the data in the database right,
# don't expect cobbler to validate it or otherwise fix it.


import cobbler.api

from server.codes import *
from server import config_data
from server import logger

import baseobj
import config
import deployment
import distribution
import profile
import machine
import web_svc

import os
import threading
import traceback

#--------------------------------------------------------------------

ENOROOT = """
\nThe provisioning components typically require root access.  If you
encounter errors, switch to root.\n
"""

NOW_CONFIGURING = """\n
Now configuring the provisioning subcomponent using settings from %s\n
"""

MIRROR_EXITED = """
\nMirror import exited.  Now imported distributions can be added 
to Virt-factory.  Note any errors above, you may have to 
reconfigure the mirror list in %s if a mirror path was invalid
or the chosen mirror was down.\n
"""

MIRROR_INFO = """
\nProcessing rsync mirror named: %s
Address                      : %s\n
"""

NOW_SAVING = """
\nNow saving the temporary provisioning configuration.\n
"""

NOW_IMPORTING = """
\nNow importing configured mirrors.  This may take a relatively long amount of time.\n
"""

NOW_ADDING = """ 
\nNow adding distribution to virt-factory.\n
   name:         %s
   kernel:       %s
   initrd:       %s
   architecture: %s\n
"""

FINISHED = """
\nUnless there's an error above somewhere, we're done with virt-factory
imports.  Virt-factory is now set up for provisioning.
     
Should you want to add different distributions, you can update your mirror list and
run "vf_server import" at a later date with additional rsync mirrors. 

Now log in through the Web UI...  You're good to go.\n
"""

def input_string_or_hash(options,delim=","):
    """
    Borrowed from cobbler, this allows the kickstart metadata options to be more
    flexible in regards to input data -- which  may be in the DB as a string and
    is entered here in hash form. 
    """
    if options is None:
        return (True, {})
    elif type(options) != dict:
        new_dict = {}
        tokens = options.split(delim)
        for t in tokens:
            tokens2 = t.split("=")
            if len(tokens2) == 1 and tokens2[0] != '':
                new_dict[tokens2[0]] = None
            elif len(tokens2) == 2 and tokens2[0] != '':
                new_dict[tokens2[0]] = tokens2[1]
            else:
                return (False, {})
        new_dict.pop('', None)
        return (True, new_dict)
    else:
        options.pop('',None)
        return (True, options)


#--------------------------------------------------------------------

class CobblerTranslatedDistribution:
   def __init__(self,cobbler_api,from_db):
       if from_db.has_key("id") and from_db["id"] < 0:
           return
       new_item = cobbler_api.new_distro()
       new_item.set_name(from_db["name"])
       new_item.set_kernel(from_db["kernel"])
       new_item.set_initrd(from_db["initrd"])
       if from_db.has_key("kernel_options"):
           new_item.set_kernel_options(from_db["kernel_options"])
       new_item.set_arch(COBBLER_ARCH_MAPPING[from_db["architecture"]])
       ks_meta = {}
       if from_db.has_key("kickstart_metadata"):
           (rc, ks_meta) = input_string_or_hash(from_db["kickstart_metadata"])
       cobbler_api.distros().add(new_item, with_copy=True)
       cobbler_api.serialize()

#--------------------------------------------------------------------

class CobblerTranslatedProfile:
   def __init__(self,cobbler_api,distributions,from_db):

       if from_db.has_key("id") and from_db["id"] < 0:
           return
       
       vf_config = config_data.Config().get()

       new_item = cobbler_api.new_profile()
       new_item.set_name(from_db["name"])
       
       distribution_id = from_db["distribution_id"]
       distribution_name = None
       
       distribution_obj = distribution.Distribution()
       distrib = distribution_obj.get(None, { "id" : distribution_id })
       if distrib.ok():
            distribution_name = distrib.data["name"]

       new_item.set_distro(distribution_name)

       # intentional.
       # use the same kickstart template for all profiles but template it out based on
       # distro, profile, and system settings. 
       new_item.set_kickstart("/var/lib/virt-factory/kick-fc6.ks")

       if from_db.has_key("kernel_options"):
           new_item.set_kernel_options(from_db["kernel_options"])
       
       virt_size = 0
       virt_ram  = 0
       if from_db.has_key("virt_storage_size"):
           virt_size = from_db["virt_storage_size"]
       if from_db.has_key("virt_ram"):
           virt_ram  = from_db["virt_ram"]

       new_item.set_virt_file_size(virt_size)
       new_item.set_virt_ram(virt_ram)


       ks_meta = {}
       if from_db.has_key("kickstart_metadata"):
           (rc, ks_meta) = input_string_or_hash(from_db["kickstart_metadata"])

        
       # user will have to create vf_repo manually ATM
       ks_meta["node_common_packages"] = "koan puppet virt-factory-nodes virt-factory-register" 
       ks_meta["node_virt_packages"] = ""
       ks_meta["node_bare_packages"] = ""
       if from_db.has_key("is_container") and from_db["is_container"] != 0:
           # FIXME: is this package list right?
           ks_meta["node_virt_packages"]   = "xen libvirt python-libvirt python-virstinst"  
           ks_meta["node_bare_packages"]   = ""
       ks_meta["extra_post_magic"]     = ""

       ks_meta["cryptpw"]              = "$1$mF86/UHC$WvcIcX2t6crBz2onWxyac." # FIXME
       ks_meta["token_param"]          = "--token=UNSET" # intentional, system can override
       ks_meta["repo_line"]  = "repo --name=vf_repo --baseurl http://%s/vf_repo" % vf_config["this_server"]["address"]
       ks_meta["server_param"] = "--server=http://%s:5150" % vf_config["this_server"]["address"] 
       ks_meta["server_name"] = vf_config["this_server"]["address"] 

       # Calculate the kickstart tree location from the distro.
       distribution_name = distrib.data["name"]
       cobbler_distro = cobbler_api.distros().find(distribution_name)
       if cobbler_distro is None:
           assert("no cobbler distro named %s" % distribution_name)
       kernel_path = cobbler_distro.kernel
       print kernel_path
       tree_path = kernel_path.split("/")[0:-3]
       print tree_path
       tree_path = "/".join(tree_path)
       print tree_path
       tree_url = tree_path.replace("/var/www/cobbler/ks_mirror","http://%s/cobbler_track/ks_mirror" % vf_config["this_server"]["address"])
       ks_meta["tree"] = tree_url 
 
       new_item.set_ksmeta(ks_meta)
      
       cobbler_api.profiles().add(new_item, with_copy=True)
       cobbler_api.serialize()

#--------------------------------------------------------------------

# FIXME: note that asserts don't work in XMLRPCServer
# and need to replace with exceptions.  Also for some
# reason profile_name is ending up as None, and this needs
# to be fixed.

def cobbler_remove_system(cobbler_api, from_db):
   try:
       if from_db.has_key("mac_address"):
           cobbler_api.systems().remove(from_db["mac_address"])
           cobbler_api.serialize()
   except:
       # this exception might be ok...
       traceback.print_exc()

class CobblerTranslatedSystem:
   def __init__(self,cobbler_api,profiles,from_db,is_virtual=False):
       
       if from_db.has_key("id") and from_db["id"] < 0:
           print "my ID is less than 0"
           return

       self.logger = logger.Logger().logger

       self.logger.debug("from_db is ...")
       self.logger.debug(from_db)
       print "***************"
       print from_db
       if not from_db.has_key("mac_address") or from_db["mac_address"] is None:
           # ok to have a record of it, just not in cobbler ...
           self.logger.debug("this system has no mac, no not cobblerfying")
           return
 
       vf_config = config_data.Config().get()

       # cobbler systems must know their profile.
       # we get a profile by seeing if a deployment references
       # the system.  
 
       if from_db.has_key("id") and from_db["id"] < 0:
           self.logger.debug("not cobblerfying because db id < 0")
           # remove if already there
           # cobbler_remove_system(cobbler_api, from_db)
           return

       if not from_db.has_key("profile_id"):
           # what happened here is that the machine was registered but no profile is 
           # assigned by the user in GUI land, so until that happens it can't be 
           # provisioned.  This is /NOT/ neccessarily an error condition.
           self.logger.debug("not cobblerfying because no profile_id")
           # remove if already there
           cobbler_remove_system(cobbler_api, from_db)
           return

       profile_id = from_db["profile_id"]

       print "this machine has profile_id = %s" % profile_id

       # FIXME: inefficient, again, write some query stuff here.
       # cobbler is going to need the name of the profile.
       profile_name = None
       print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
       for i in profiles:
           if i["id"] == profile_id:
               print "MATCHED:", i
               profile_name = i["name"] 
               break

       if profile_name == None:
           print "name not found"
           return # can't deploy this

       new_item = cobbler_api.new_system()
       new_item.set_name(from_db["mac_address"])
       self.logger.debug("cobbler profile name is %s" % profile_name)
       new_item.set_profile(profile_name)
       # FIXME: do we need to make sure these are stored as spaces and not "None" ?
       
       kernel_options = ""
       # kickstart_metadata = ""
       pxe_address = ""

       if from_db.has_key("kernel_options"):
           kernel_options = from_db["kernel_options"]

       ks_meta = {}
       if from_db.has_key("kickstart_metadata"):
           # kickstart_metadata = from_db["kickstart_metadata"]
           # load initial kickstart metadata (which is a string) and get back a hash
           (success, ksmeta) = input_string_or_hash(from_db["kickstart_metadata"], " ")
       ks_meta["server_param"] = "--server=http://%s:5150" % vf_config["this_server"]["address"] 
       ks_meta["server_name"] = vf_config["this_server"]["address"] 
       ks_meta["token_param"] = "--token=%s" % from_db["registration_token"]

       # FIXME: be sure this field name corresponds with the new machine/deployment field
       # once it is added.
       if from_db.has_key("ip_address"):
           pxe_address = from_db["ip_address"]

       # FIXME: deal with is_virtual


       new_item.set_kernel_options(kernel_options)
       new_item.set_ksmeta(ks_meta)
       
       if from_db.has_key("netboot_enabled"):
           new_item.set_netboot_enabled(from_db["netboot_enabled"])
       else:
           new_item.set_netboot_enabled(False)

       if pxe_address != "":
           new_item.set_pxe_address(pxe_address)
       
       if from_db.has_key("netboot_enabled"):
           new_item.set_netboot_enabled(from_db["netboot_enabled"])
       else:
           new_item.set_netboot_enabled(False)

       
       cobbler_api.systems().add(new_item, with_copy=True)
       cobbler_api.serialize()
       self.logger.debug("cobbler system serialized")

#--------------------------------------------------------------------

# FIXME: need another virt-factory backend object that will need to sync with
# /var/lib/cobbler/settings

class Provisioning(web_svc.AuthWebSvc):
   def __init__(self):
      self.methods = {"sync": self.sync,
                      "init": self.init}
      web_svc.AuthWebSvc.__init__(self)                      
      

   def sync(self, token, prov_args):
         

      self.distribution = distribution.Distribution()
      distributions = self.distribution.list(token, {})

      self.profile = profile.Profile()
      profiles = self.profile.list(token, {})

      self.machine = machine.Machine() 
      machines  = self.machine.list(token, {})

      self.deployment = deployment.Deployment()
      deployments = self.deployment.list(token, {})      

      # cobbler does do it's own locking, but not for API users...
      lock = threading.Lock()
      lock.acquire()
      
      distributions = distributions.data
      profiles      = profiles.data
      machines      = machines.data
      deployments   = deployments.data
      
      # FIXME: (IMPORTANT) update cobbler config from virt-factory config each time, in particular,
      # the server field might have changed.
      
      try:
         cobbler_api = cobbler.api.BootAPI()
         cobbler_api.sync()
         cobbler_distros  = cobbler_api.distros()
         cobbler_profiles = cobbler_api.profiles()
         cobbler_systems  = cobbler_api.systems()
         cobbler_distros.clear()
         cobbler_profiles.clear()
         cobbler_systems.clear()
         
         # cobbler can/will could raise exceptions on failure at any point...
         # return code checking is not needed.
         for d in distributions:
            print "- distribution: %s" % d
            CobblerTranslatedDistribution(cobbler_api,d)
         for i in profiles:
            print "- profile: %s" % i
            CobblerTranslatedProfile(cobbler_api,distributions,i)
         for p in machines:
            print "- machine: %s" % p
            CobblerTranslatedSystem(cobbler_api,profiles,p)
         for dp in deployments:
            print "- deployment: %s" % dp
            CobblerTranslatedSystem(cobbler_api,profiles,dp)

         cobbler_api.serialize()
         cobbler_api.sync()
      except:
         traceback.print_exc() # FIXME: really we want to log this
         lock.release()
         raise UncaughtException(traceback=traceback.format_exc())


      lock.release()
      return success()


   def init(self, token, prov_args):

        """
        Bootstrap virt-factory's distributions list by pointing cobbler at an rsync mirror.
        """


        ARCH_CONVERT = {
           "x86"    : ARCH_X86,
           "x86_64" : ARCH_X86_64,
           "ia64"   : ARCH_IA64
        }

        lock = threading.Lock()
        lock.acquire()

        if os.getuid() != 0:

            print ENOROOT 


        cobbler_api = cobbler.api.BootAPI()
        # since cobbler is running in syncless mode, make sure sync
        # has been run at least once with an empty config to create
        # directories
        cobbler_api.sync()
        settings = cobbler_api.settings().to_datastruct()
        vf_config = self.config


        # FIXME: probably should just except on config read failures
#        if not config_results.ok():
#            raise VirtFactoryException(comment="config retrieval failed")
#        vf_config = config_results.data

        print NOW_CONFIGURING % config_data.CONFIG_FILE

        settings["server"] = vf_config["this_server"]["address"]
        settings["next_server"] = vf_config["this_server"]["address"]
        # FIXME: load other defaults that the user might want to configure in cobbler

        print NOW_SAVING

        cobbler_api.serialize() 

        print NOW_IMPORTING

        # FIXME

        # read the config entry to find out cobbler's mirror locations
        for mirror_name in vf_config["mirrors"]:

           mirror_url = vf_config["mirrors"][mirror_name]

           print MIRROR_INFO % (mirror_name, mirror_url)


           # run the cobbler mirror import
           # FIXME: more of a cobbler issue, but cobbler needs 
           # to detect rsync failures such as mirrors that are shut down
           # but don't have any files available.

           cobbler_api.import_tree(mirror_url,mirror_name)

           print MIRROR_EXITED

        cobbler_api.serialize()

        # go through the distribution list in cobbler and make virt-factory distribution entries
        cobbler_distros = cobbler_api.distros()

        for distro in cobbler_distros:
           distro_data = distro.to_datastruct()
           kernel = distro_data["kernel"]
           initrd = distro_data["initrd"]
           name   = distro_data["name"]
           arch   = ARCH_CONVERT[distro_data["arch"].lower()]

           print NOW_ADDING % (name, kernel, initrd, arch)

           # FIXME: this code will generally break on duplicate names, so we really want to do a distribution_list to
           # see if any exist prior to add.  (can't do a get, because that's id based... kind of prompts a find_by_name
           # later, most likely)

           add_data =  {
              "kernel" : kernel,
              "initrd" : initrd,
              "name"   : name,
              "architecture" : arch,
              "options" : "",

              # this next line doesn't account for the possibility of one kickstart not being enough for different
              # distros.  If this becomes an issue, I'd recommend Cobbler templating be used for those parts, rather
              # than having to specify a kickstart file on distro import.  Preferably we keep distro kickstarts
              # very simple and don't use a lot of fancy features for them, though this could get complicated later.
              # something to watch.  It may be that the virt-factory config file needs to specify both the
              # rsync mirror and the kickstart, though this probably asks a bit too much of the person installing
              # the app.  Another way to do this (similar to what cobbler does on import) is to look at the
              # path and try to guess.  It's a bit error prone, but workable for mirrors that have a known
              # directory structure.  See cobbler's action_import.py for that.

              "kickstart" : "/var/lib/virt-factory/kick-fc6.ks",
              "kickstart_metadata" : ""
           }
           print "cobbler distro add: %s" % add_data


           try:
              dist = distribution.Distribution()
              dist.add(token, add_data)
           except SQLException, se:
               # if running import again to acquire new distros, the add could result in a duplicate data item.
               # this allows for such problems, as caught by the UNIQUE constraint on the distro name.       
               # note that if this happens, we can't delete and re-add as other things might be depending on the distro.
               # though there shouldn't be any fields we want to change.  As a result, we'll just ignore the error
               # if it's one from the SQL insert, which is normally tested to work.  Other exceptions need to go through.
               pass  

           # don't have to delete the cobbler distribution entries as they are going to be rewritten
           # on sync (with similar data)


        # now the records are in the table, and we won't be reading cobbler config data again ...
        # we'll just be writing it.  The distribution bootstrapping is complete.

        print FINISHED

        lock.release()
        return success()


methods = Provisioning()
register_rpc = methods.register_rpc


