#!/usr/bin/python
"""
sm_import is a utility script which imports an image profile from an
appliance definition file.

Image profiles should be a self-contained tarball with the following directory structure:
	profilename/profile.xml  -- includes metadata needed for adding to SM database.
	profilename/manifests/*.pp  -- includes puppet manifests, can be named anything
	profilename/files/* -- includes data files referenced by manifests
 	profilename/templates/* -- includes templates referenced by manifests

Each execution of the sm_import tool will do the following:

	Use the XML data to insert a row into the images database IF it's not already imported
	Import the manifests to /var/lib/shadowmanager/profiles/$image-name/manifests/*
	Import the data files to /var/lib/shadowmanager/profiles/$image-name/files/*
	Import the templates files to /var/lib/shadowmanager/profiles/$image-name/templates/*
	Update the site-wide puppet manifest as necessary

NOTE: this can only be run after the initial "shadow import", because
      distributions are needed in order to import image profiles. 

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
import tarfile
import traceback
import types
from xml.dom.minidom import parse, parseString

import codes
import logger
logger.logfilepath = "/var/lib/shadowmanager/sm_import.log"
from modules import distribution
from modules import image

# TODO: should go in /var/lib/puppet/config/lib once puppet modules work
PUPPET_FILE_DIR="/var/lib/shadowmanager/profiles"
PUPPET_SITE_MANIFEST="/etc/puppet/manifests/site.pp"
PUPPET_FILESERVER_CONF="/etc/puppet/fileserver.conf"

PROFILE_REGEXP = "profile\.xml$"
NAME_TAG = "name"
VERSION_TAG = "version"
DISTRIBUTION_TAG = "distribution"
VIRT_STORAGE_SIZE_TAG = "virt_storage_size"
VIRT_RAM_TAG = "virt_ram"
KICKSTART_METADATA_TAG = "kickstart_metadata"
KERNEL_OPTIONS_TAG = "kernel_options"
VALID_TARGETS_TAG = "valid_targets"
IS_CONTAINER_TAG = "is_container"
PUPPET_CLASSES_TAG = "puppet_classes"

DISTRIBUTION_ID_TAG = "distribution_id"

class ShadowImporter:
   """
   Main class for sm_import tool
   """

   def __init__(self, tarball):
       """
       create importer object -- source tarball is passed in
       """
       if (not tarfile.is_tarfile(tarball)):
           raise ValueError(tarball + " is not a tarfile")
       self.tarball_path = tarball
       log = logger.Logger()
       self.logger = log.logger

   def extract(self):
        self.tarball = tarfile.open(self.tarball_path)

        for member in self.tarball.getmembers():
            if (re.search(PROFILE_REGEXP, member.name)):
                print "excluding ", member.name
                self.profile = self.tarball.extractfile(member)
            else:
                print "extracting ", member.name
                self.tarball.extract(member, PUPPET_FILE_DIR)

   def populate_sm_profile(self):
       profiledoc = parse(self.profile)
       profile_dict = {}
       
       self.set_node_text(profiledoc, profile_dict, NAME_TAG)
       self.set_node_text(profiledoc, profile_dict, VERSION_TAG)
       self.set_node_text(profiledoc, profile_dict, VIRT_STORAGE_SIZE_TAG, "int")
       self.set_node_text(profiledoc, profile_dict, VIRT_RAM_TAG, "int")
       self.set_node_text(profiledoc, profile_dict, KICKSTART_METADATA_TAG)
       self.set_node_text(profiledoc, profile_dict, KERNEL_OPTIONS_TAG)
       self.set_node_text(profiledoc, profile_dict, VALID_TARGETS_TAG)
       self.set_node_text(profiledoc, profile_dict, IS_CONTAINER_TAG, "int")
       self.set_node_text(profiledoc, profile_dict, PUPPET_CLASSES_TAG)
       distribution_name = self.get_node_text(profiledoc, DISTRIBUTION_TAG)
       if (distribution_name is not None):
           distribution_obj = distribution.Distribution()
           distribution_result = distribution_obj.get_by_name(None, {"name": "var_www_cobbler_ks_mirror_FC-6_GOLD_i386_os_images_pxeboot"})
           if (distribution_result.error_code != 0):
               raise codes.InvalidArgumentsException(comment="bad distribution name")
           profile_dict[DISTRIBUTION_ID_TAG] = distribution_result.data["id"]
       image_obj = image.Image()
       try:
           result = image_obj.add(None, profile_dict)
       except Exception, e:
           print "error adding image: "
           (t, v, tb) = sys.exc_info()
           self.logger.debug("Exception occured: %s" % t )
           self.logger.debug("Exception value: %s" % v)
           self.logger.debug("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))

       
   def get_node_text(self, profiledoc, name):
       children = profiledoc.getElementsByTagName(name)[0].childNodes
       if (len(children)>0):
           return children[0].data
       else:
           return None
       
   def set_node_text(self, profiledoc, profile_dict, name, convert=None):
       value = self.get_node_text(profiledoc, name)
       if (value is not None):
           if (convert=="int"):
               value = int(value)
           profile_dict[name] = value

#--------------------------------------------------------------------------
      
def main(argv):
    """
    Start things up.
    """
    
    usage = "usage: %prog [options] appliance-spec-file"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--module-dir", dest="module",
                      help="top-level puppet module directory",
                      default=PUPPET_FILE_DIR)
    parser.add_option("-m", "--site-wide-manifest", dest="manifest",
                      help="puppet site-wide manifest",
                      default=PUPPET_SITE_MANIFEST)
    parser.add_option("-f", "--fileserver-conf", dest="fileserver_conf",
                      help="puppet fileserver configuration file",
                      default=PUPPET_FILESERVER_CONF)
    
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")    
    importer = ShadowImporter(args[1])
    print "extracting..."
    importer.extract()
    print "populating..."
    importer.populate_sm_profile()
    # TODO: modify puppet site.pp and/or file manager config

if __name__ == "__main__":
    main(sys.argv)


