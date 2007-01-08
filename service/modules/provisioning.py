#!/usr/bin/python
## ShadowManager backend code.
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
# things like image and deployments, etc.

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

from codes import *

import baseobj
import config
import deployment
import distribution
import image
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
to ShadowManager.  Note any errors above, you may have to 
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
\nNow adding distribution to ShadowManager.\n
   name:         %s
   kernel:       %s
   initrd:       %s
   architecture: %s\n
"""

FINISHED = """
\nUnless there's an error above somewhere, we're done with ShadowManager 
imports.  ShadowManager is now set up for provisioning.
     
Should you want to add different distributions, you can update your mirror list and
run "shadow import" at a later date with additional rsync mirrors. 

Now log in through the Web UI...  You're good to go.\n
"""

#--------------------------------------------------------------------

class CobblerTranslatedDistribution:
   def __init__(self,cobbler_api,from_db):
       new_item = cobbler_api.new_distro()
       new_item.set_name(from_db["name"])
       new_item.set_kernel(from_db["kernel"])
       new_item.set_initrd(from_db["initrd"])
       if from_db.has_key("kernel_options"):
           new_item.set_kernel_options(from_db["kernel_options"])
       new_item.set_arch(codes.COBBLER_ARCH_MAPPING[from_db["architecture"]])
       if from_db.has_key("kickstart_metadata"):
           new_item.set_ksmeta(from_db["kickstart_metadata"])
       cobbler_api.distros().add(new_item)

#--------------------------------------------------------------------

class CobblerTranslatedProfile:
   def __init__(self,cobbler_api,distributions,from_db):
       new_item = cobbler_api.new_profile()
       new_item.set_name(from_db["name"])
       
       distribution_id = from_db["distribution_id"]
       distribution_name = None
       for d in distributions:
           if d["id"] == distribution_id:
               distribution_name = d["name"]
               break    

       assert distribution_name is not None, "has distribution name"

       new_item.set_distro(distribution_name)

       if from_db.has_key("kickstart"):
           new_item.set_kickstart(from_db["kickstart"])
       if from_db.has_key("kernel_options"):
           new_item.set_kernel_options(from_db["kernel_options"])
       
       new_item.set_virt_name(from_db["name"])
       
       virt_size = 0
       virt_ram  = 0
       if from_db.has_key("virt_storage_size"):
           virt_size = from_db["virt_storage_size"]
       if from_db.has_key("virt_ram"):
           virt_ram  = from_db["virt_ram"]

       new_item.set_virt_file_size(virt_size)
       new_item.set_virt_ram(virt_ram)


       if from_db.has_key("kickstart_metadata"):
           new_item.set_ksmeta(from_db["kickstart_metadata"])
       cobbler_api.profiles().add(new_item)

#--------------------------------------------------------------------

class CobblerTranslatedSystem:
   def __init__(self,cobbler_api,deployments,images,from_db):
       # cobbler systems must know their profile.
       # we get a profile by seeing if a deployment references
       # the system.  
 
       machine_id = from_db["id"]

       
       # FIXME: custom query code is needed in places like this,
       # processing flat lists won't scale well for really large
       # deployments
       image_id = -1
       for d in deployments:
           if d["machine_id"] == machine_id:
               image_id = d["image_id"]
               break               

       if image_id == -1:
          # no deployment found for this machine, which means
          # we have no idea how to provision it.  it should
          # at least have a APPLIANCE_CONTAINER or ORDINARY_MACHINE
          # deployment set up for it.
          assert "no image id found for system"

       # FIXME: inefficient, again, write some query stuff here.
       image_name = None
       for i in images:
           if i["id"] == image_id:
               image_name = i["name"] 
               break

       if image_name == None:
           assert "no image name found"

       new_item = cobbler_api.new_system()
       new_item.set_name(from_db["mac_address"])
       print "image name is %s" % image_name
       new_item.set_profile(image_name)
       # FIXME: do we need to make sure these are stored as spaces and not "None" ?
       new_item.set_kernel_options(from_db["kernel_options"])
       new_item.set_ksmeta(from_db["kickstart_metadata"])
       new_item.set_pxe_address(from_db["address"])
       cobbler_api.systems().add(new_item)

#--------------------------------------------------------------------

# FIXME: need another ShadowManager backend object that will need to sync with
# /var/lib/cobbler/settings

class Provisioning(web_svc.AuthWebSvc):
   def __init__(self):
      self.methods = {"provisioning_sync": self.sync,
                      "provisioning_init": self.init}
      web_svc.AuthWebSvc.__init__(self)                      

   def sync(self, prov_args):

        distributions       = distribution.distribution_list(websvc,{})
        images              = image.image_list(websvc,{})
        machines            = machine.machine_list(websvc,{})
        deployments         = deployment.deployment_list(websvc, {})

        # cobbler can't be run multiple times at once...
        lock = threading.Lock()
        lock.acquire()

        distributions = distributions.data
        images = images.data
        machines = machines.data
        deployments = deployments.data

        # FIXME: (IMPORTANT) update cobbler config from shadowmanager config each time, in particular,
        # the server field might have changed.

        try:
            cobbler_api = cobbler.api.BootAPI()
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
            for i in images:
                print "- image: %s" % i
                CobblerTranslatedProfile(cobbler_api,distributions,i)
            for p in machines:
                print "- machine: %s" % p
                CobblerTranslatedSystem(cobbler_api,deployments,images,p)
            cobbler_api.serialize()
            cobbler_api.sync(dryrun=False)
        except:
            traceback.print_exc()
            lock.release()
            raise codes.UncaughtException(traceback=traceback.format_exc())


        lock.release()
        return success()


   def init(self, prov_args):

        """
        Bootstrap ShadowManager's distributions list by pointing cobbler at an rsync mirror.
        """

        ARCH_CONVERT = {
           "x86"    : codes.ARCH_X86,
           "x86_64" : codes.ARCH_X86_64,
           "ia64"   : codes.ARCH_IA64
        }

        lock = threading.Lock()
        lock.acquire()

        if os.getuid() != 0:

            print ENOROOT 


        # create /var/lib/cobbler/settings from /var/lib/shadowmanager/settings
        cobbler_api = cobbler.api.BootAPI()
        settings = cobbler_api.settings().to_datastruct()
        config_obj = config_data.Config()
        shadow_config = config_obj.get()

        # FIXME: probably should just except on config read failures
#        if not config_results.ok():
#            raise ShadowManagerException(comment="config retrieval failed")
#        shadow_config = config_results.data

        print NOW_CONFIGURING % config_data.CONFIG_FILE

        settings["server"] = shadow_config["this_server"]["address"]
        settings["next_server"] = shadow_config["this_server"]["address"]
        # FIXME: load other defaults that the user might want to configure in cobbler

        print NOW_SAVING

        cobbler_api.serialize() 

        print NOW_IMPORTING

        # FIXME

        # read the config entry to find out cobbler's mirror locations
        for mirror_name in shadow_config["mirrors"]:

           mirror_url = shadow_config["mirrors"][mirror_name]

           print MIRROR_INFO % (mirror_name, mirror_url)


           # run the cobbler mirror import
           # FIXME: more of a cobbler issue, but cobbler needs 
           # to detect rsync failures such as mirrors that are shut down
           # but don't have any files available.

           cobbler_api.import_tree(None,mirror_url,mirror_name)

           print MIRROR_EXITED

        cobbler_api.serialize()

        # go through the distribution list in cobbler and make shadowmanager distribution entries
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
              # something to watch.  It may be that the shadowmanager config file needs to specify both the
              # rsync mirror and the kickstart, though this probably asks a bit too much of the person installing
              # the app.  Another way to do this (similar to what cobbler does on import) is to look at the
              # path and try to guess.  It's a bit error prone, but workable for mirrors that have a known
              # directory structure.  See cobbler's action_import.py for that.

              "kickstart" : "/etc/shadowmanager/default.ks",
              "kickstart_metadata" : ""
           }
           print "cobbler distro add: %s" % add_data


           try:
               distribution.distribution_add(websvc,add_data)
           except SQLException, se:
               # if running import again to acquire new distros, the add could result in a duplicate data item.
               # this allows for such problems, as caught by the UNIQUE constraint on the distro name.       
               # note that if this happens, we can't delete and re-add as other things might be depending on the distro.
               # though there shouldn't be any fields we want to change.  As a result, we'll just ignore the error
               # if it's one from the SQL insert, which is normally tested to work.  Other exceptions need to go through.
               pass  

           # don't have to delete the cobbler distribution entries as they are going to be rewritten
           # on provisioning_sync (with similar data)


        # now the records are in the table, and we won't be reading cobbler config data again ...
        # we'll just be writing it.  The distribution bootstrapping is complete.

        print FINISHED

        lock.release()
        return success()


methods = Provisioning()
register_rpc = methods.register_rpc

