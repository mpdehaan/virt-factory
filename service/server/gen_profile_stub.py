#!/usr/bin/python

"""
gen_profile_stub: generates initial build and file template for a profile

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Adrian Likins <alikins@redhat.com>
Scott Seago <sseago@redhat.com>

XMLRPCSSL portions based on http://linux.duke.edu/~icon/misc/xmlrpcssl.py

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

from optparse import OptionParser
import os
import re
import shutil
import sys

from Cheetah.Template import Template


class GenProfileStub(object):
   def __init__(self, options):
       self.name = options.name
       self.version = options.version
       self.release = options.release
       self.storage = options.storage
       self.distribution = options.distribution
       self.ram = options.ram
       self.ksmetadata = options.ksmetadata
       self.koptions = options.koptions
       self.targets = options.targets
       self.container = options.container
       self.puppetclasses = options.puppetclasses

   def generate(self):
       self.gen_profile_dirs()
       self.gen_version_file()
       self.copy_template_files()
       
   def gen_profile_dirs(self):
       os.mkdir(self.name)
       os.mkdir(self.name + "/manifests")
       os.mkdir(self.name + "/files")
       os.mkdir(self.name + "/templates")
       
   def gen_version_file(self):
       version_str = self.name + " " + self.version + " " + self.release + "\n"
       fd1 = open(self.name + "/version","w+")
       fd1.write(version_str)
       fd1.close()

   def copy_template_files(self):
       shutil.copy("/usr/share/virt-factory/profile-template/Makefile", self.name)
       shutil.copy("/usr/share/virt-factory/profile-template/vf-profile-template.spec", self.name + "/vf-profile-" + self.name + ".spec")
       print "Edit spec file and fill in Summary, description, and changelog"
       shutil.copy("/usr/share/virt-factory/profile-template/init.pp", self.name + "/manifests")
       template_file = open("/usr/share/virt-factory/profile-template/profile.xml.in","r")
       template_data = template_file.read()
       template_file.close()
       metadata = {
           "name" : self.name,
           "version" : self.version,
           "release" : self.release,
           "storage" : self.storage,
           "distribution" : self.distribution,
           "ram" : self.ram,
           "ksmetadata" : self.ksmetadata,
           "koptions" : self.koptions,
           "targets" : self.targets,
           "container" : self.container,
           "puppetclasses" : self.puppetclasses
       }
       self.apply_template(template_data, metadata, self.name + "/profile.xml")

   def apply_template(self, data_input, metadata, out_path):
       """
       Take filesystem file profile.xml, apply metadata using
       Cheetah and save as out_path.
       """


       if type(data_input) != str:
           data = data_input.read()
       else:
           data = data_input

       data = "#errorCatcher Echo\n" + data
       
       t = Template(source=data, searchList=[metadata])
       data_out = str(t)
       if out_path is not None:
           #os.makedirs(os.path.dirname(out_path))
           fd = open(out_path, "w+")
           fd.write(data_out)
           fd.close()
       return data_out


#--------------------------------------------------------------------------

def main(argv):
    """
    Start things up.
    """
    usage = "usage: %prog [options] "
    parser = OptionParser(usage=usage)
    parser.add_option("-n", "--name", dest="name",
                      help="profile name")
    parser.add_option("-v", "--version", dest="version",
                      help="profile version",
                      default="0.0.1")
    parser.add_option("-r", "--release", dest="release",
                      help="profile rpm release",
                      default="1")
    parser.add_option("-d", "--distribution", dest="distribution",
                      help="profile distribution",
                      default="")
    parser.add_option("-s", "--storage", dest="storage",
                      help="profile virt storage size",
                      default="")
    parser.add_option("-m", "--ram", dest="ram",
                      help="profile virt ram",
                      default="")
    parser.add_option("-k", "--ksmetadata", dest="ksmetadata",
                      help="profile kickstart metadata",
                      default="")
    parser.add_option("-o", "--koptions", dest="koptions",
                      help="profile kernel options",
                      default="")
    parser.add_option("-t", "--targets",
                      dest="targets", type="choice", choices=["is_virt", "is_baremetal", "is_either"], default=None,
                      help="Valid target type for the profile (i.e. for virt vs. baremetal provisioning).")
    parser.add_option("-c", "--container",
                      dest="container", type="choice", choices=["0", "1"], default="0",
                      help="Whether a host running this profile is a valid target for VM guests.")
    parser.add_option("-p", "--puppetclasses", dest="puppetclasses",
                      help="profile puppet classes",
                      default="")

    (options, args) = parser.parse_args()
    if not options.name:
        parser.error("name is required")
    else:
        match = re.search("\W+", options.name)
        if match:
            print "profile name must contain only alphanumeric characters and underscores. Specified name includes '" + match.group() + "'"
            sys.exit(1)

    gen_profile = GenProfileStub(options)
    gen_profile.generate();
    
if __name__ == "__main__":
    main(sys.argv)


