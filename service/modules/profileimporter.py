"""
vf_import_profile is a utility script which imports previously installed
profile packages.

For profile format information see:
    http://virt-factory.et.redhat.com/vf-profile-format.php

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Adrian Likins <alikins@redhat.com>
Scott Seago <sseago@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""


from optparse import OptionParser
import re
import string
import sys
import os
import tarfile
import tempfile
import traceback
import types
from xml.dom.minidom import parse, parseString
from urllib import urlretrieve

from server.config_data import *
from server.codes import *
from server import logger
import distribution
import profile
import provisioning
from server.db import Database

# TODO: should go in /var/lib/puppet/config/lib once puppet modules work
PUPPET_FILE_DIR="/var/lib/virt-factory/profiles"
PUPPET_QUEUED_FILE_DIR="queued"
PUPPET_SITE_MANIFEST="/etc/puppet/manifests/site.pp"

NAME_TAG = "name"
VERSION_TAG = "version"
DISTRIBUTION_TAG = "distribution"
VIRT_STORAGE_SIZE_TAG = "virt_storage_size"
VIRT_RAM_TAG = "virt_ram"
VIRT_TYPE_TAG = "virt_type"
KICKSTART_METADATA_TAG = "kickstart_metadata"
KERNEL_OPTIONS_TAG = "kernel_options"
VALID_TARGETS_TAG = "valid_targets"
IS_CONTAINER_TAG = "is_container"
PUPPET_CLASSES_TAG = "puppet_classes"

DISTRIBUTION_ID_TAG = "distribution_id"

# FIXME: this class needs more comments

class ProfileImporter:
    def __init__(self, log, module_name=None, force_all=False,
                 module_dir=PUPPET_FILE_DIR, manifest=PUPPET_SITE_MANIFEST):
        """
        create importer object -- source tarball is passed in
        """
        if force_all:
            self.module_names = os.listdir(module_dir)
            if self.module_names.count(PUPPET_QUEUED_FILE_DIR) > 0:
                self.module_names.remove(PUPPET_QUEUED_FILE_DIR)
        elif module_name:
            self.module_names = [module_name]
        else:
            self.module_names = os.listdir(module_dir + "/" + PUPPET_QUEUED_FILE_DIR)
                
        self.logger=log
        self.profile_importers = {}
        for name in self.module_names:
            self.profile_importers[name] = OneProfileImporter(name,
                                                              module_dir,
                                                              manifest,
                                                              log)
                    
    def run_import(self):
        for profile in self.profile_importers.values():
            profile.run_import()
        prov = provisioning.Provisioning()
        prov.sync(None, None)

class OneProfileImporter:
   """
   Main class for sm_import tool
   """

   def __init__(self, module_name, module_dir, manifest, log):
       """
       create importer object -- source tarball is passed in
       """
       self.module_name = module_name
       self.module_dir = module_dir
       self.manifest = manifest
       self.logger=log
       self.profile = parse(self.module_dir + '/' + self.module_name + "/profile.xml")

   def run_import(self):
       self.update_puppet_manifest()
       print "populating..."
       self.populate_sm_profile()
       pending_marker = self.module_dir + '/' + PUPPET_QUEUED_FILE_DIR + '/' + self.module_name
       if os.path.exists(pending_marker):
           os.remove(pending_marker)

   def update_puppet_manifest(self):
       # import_str should be simply "import profile_name" once
       # puppet module support is in place
       import_str = 'import "' + self.module_name + '"'
       
       if not self.search_for_in_file(self.manifest, import_str):
           print "appending ", import_str
           manifest_file = open(self.manifest, 'a')
           manifest_file.write('\n' + import_str + '\n')
           manifest_file.close();


   def search_for_in_file(self, filename, search_str):
       file = open(filename)
       found = 0
       for line in file:
           if re.search(search_str, line):
               found = 1
               break
       file.close()
       return found
       
   def load_profile_dict(self,profile_dict):
       self.set_node_text(profile_dict, NAME_TAG)
       self.set_node_text(profile_dict, VERSION_TAG)
       self.set_node_text(profile_dict, VIRT_STORAGE_SIZE_TAG, "int")
       self.set_node_text(profile_dict, VIRT_RAM_TAG, "int")
       self.set_node_text(profile_dict, VIRT_TYPE_TAG)
       self.set_node_text(profile_dict, KICKSTART_METADATA_TAG)
       self.set_node_text(profile_dict, KERNEL_OPTIONS_TAG)
       self.set_node_text(profile_dict, VALID_TARGETS_TAG)
       self.set_node_text(profile_dict, IS_CONTAINER_TAG, "int")
       self.set_node_text(profile_dict, PUPPET_CLASSES_TAG)
       self.set_node_text(profile_dict, DISTRIBUTION_TAG)
       self.distribution_list_names = profile_dict[DISTRIBUTION_TAG]

   def populate_sm_profile(self):

       """
       Creates the profile record(s) for the given profile object and inserts
       them into the DB.
       """

       # we want to create multiple profile objects for all of the variant distros
       # so we split the input like "FC-6, F-7" into a list [FC-6, F-7] and then
       # for each distro (ex: F-7) we create things like:
       # FC-6-i386, FC-6-xen-i386, FC-6-xen-x86_64, FC-6-xen which are all the combinations
       # possible of Cobbler (and VF) distros that might have already been imported.
       # for ones that are NOT THERE, we don't bother creating any profile objects at 
       # all... this is totally ok.  In actuality, if we don't find ANY perspective
       # matches we will raise an error -- but just one match is ok.

       profile_dict = {}
       self.load_profile_dict(profile_dict)
       distribution_list = self.distribution_list_names.split(",")

       # the XML file contains a comma delimited list of distributions that the given
       # lightweight appliance descriptor can run on.  We're going to create multiple
       # profile records for each distro that is supported.
           
       print "scanning through: %s" % ",".join(distribution_list)

       matches = 0
       for distribution_name in distribution_list:

           # remove spaces to be tolerant of format
           print "- looking for: %s" % distribution_name
           distribution_name = distribution_name.lstrip().rstrip()

           # add all of the arches we might support if we have them imported.
           # FIXME: right now this only supports common arches, so if someone wants
           # to add ppc/ppc64 that won't fit in nicely.  However this covers nearly
           # everyone that will want to use virt-factory at this point.  IA64 may also
           # be relevant.  Should possibly include.
           combinations = [
              "%s-xen-i386" % distribution_name,
              "%s-i386" % distribution_name,
              "%s-x86_64" % distribution_name,
              "%s-xen-x86_64" % distribution_name
           ]

           # keep track of whether we have any supported distros so we can raise
           # an error if there aren't any.

           for distribution_name in combinations:


               # create a new profile object on a distro/arch specific basis
               # or modify one if it already exists

               profile_dict = {}
               self.load_profile_dict(profile_dict)

               # is this distro even in the cobbler DB?  If not, skip.

               if (distribution_name is not None):
                   distribution_obj = distribution.Distribution()
                   try:
                        distribution_result = distribution_obj.get_by_name(None, {"name": distribution_name})
                   except:
                        print "- no such distribution: %s" % distribution_name
                        continue

               if (distribution_result.error_code != 0):
                   print "- no distribution found, skipping: %s" % distribution_name
                   continue

               print "- found: %s" % distribution_name
               matches = matches + 1

               # we're going to append some data onto the profile name so it can
               # be easily parsed out by things that care.  This ideally should be done
               # by adding some additional fields (also) and populating those.  We
               # may have some of those fields already (FIXME).

               profile_dict[DISTRIBUTION_ID_TAG] = distribution_result.data["id"]
               profile_dict["name"] = profile_dict["name"] + "::" + distribution_name
               profile_obj = profile.Profile()

               # override the virt type based on the distro
               if distribution_name.find("xen") != -1:
                   profile_dict["virt_type"] = "xenpv"
               else:
                   # FIXME: if we support more than just kvm/qemu we will 
                   # want to do this slightly differently.
                   # qemu here doesn't mean qemu explicitly just things that
                   # take qemu disk images.
                   profile_dict["virt_type"] = "qemu"

               # create or modify existing
               
               self.logger.info("constructing profile record: %s" % profile_dict)
 
               try:
                   existing_profile = profile_obj.get_by_name(None, profile_dict)
                   if existing_profile.data:
                       print "modifying existing profile ", profile_dict["name"]
                       profile_dict["id"] = existing_profile.data["id"]
                       result = profile_obj.edit(None, profile_dict)
                   else:
                       print "creating new profile ", profile_dict["name"]
                       result = profile_obj.add(None, profile_dict)
               except Exception, e:
                   print "error adding profile: "
                   (t, v, tb) = sys.exc_info()
                   self.logger.error("Exception occured: %s" % t )
                   self.logger.error("Exception value: %s" % v)
                   self.logger.error("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
                   raise

       # die if we couldn't find any distro for the given profile.

       if matches == 0:
           print "- no compatible distributions have been imported for this profile: %s" % profile_dict["name"]
           sys.exit(1)

       
   def get_node_text(self, name):
       children = self.profile.getElementsByTagName(name)[0].childNodes
       if (len(children)>0):
           return children[0].data
       else:
           return None
       
   def set_node_text(self, profile_dict, name, convert=None):
       value = self.get_node_text(name)
       if (value is not None):
           if (convert=="int"):
               value = int(value)
           profile_dict[name] = value

#--------------------------------------------------------------------------
      
def main():
    """
    Start things up.
    """
    
    usage = "usage: %prog [options] [module-name]"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--module-dir", dest="module",
                      help="top-level puppet module directory",
                      default=PUPPET_FILE_DIR)
    parser.add_option("-m", "--site-wide-manifest", dest="manifest",
                      help="puppet site-wide manifest",
                      default=PUPPET_SITE_MANIFEST)
    parser.add_option("-f", "--force-all", dest="force_all",
                      action="store_true", default=False,
                      help="reload all profiles")
    
    (options, args) = parser.parse_args()
    config_obj = Config()
    config_result = config_obj.get()
    config = config_result
    databases = config['databases']
    url = databases['primary']
    Database(url)

    if len(args) > 1:
        parser.error("incorrect number of arguments")
        
    profile_in = None
    if len(args) == 1:
        profile_in = args[0]
    log = logger.Logger("/var/log/virt-factory/vf_import.log").logger
    ProfileImporter(log, profile_in, options.force_all,
                    options.module, options.manifest).run_import()

if __name__ == "__main__":
    main()
