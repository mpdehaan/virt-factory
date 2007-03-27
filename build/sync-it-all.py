#!/usr/bin/python

import os
import sys

HOST="et.redhat.com"
DISTRO="fc6"

def push(user,host,distro,release):

    if release != "stable" and release != "devel":
        raise RuntimeError, "release must be stable or devel"

    tup = (user,host,distro,release)

    cmds = [
        "/usr/bin/ssh %s@%s mkdir -p /var/www/sites/virt-factory.et.redhat.com/download/repo/%s/%s" % tup,
        "/usr/bin/rsync -rav --delete -e ssh rpms/ %s@%s:/var/www/sites/virt-factory.et.redhat.com/download/repo/%s/%s/i686/" % tup,
        "/usr/bin/rsync -rav --delete -e ssh srpms/  %s@%s:/var/www/sites/virt-factory.et.redhat.com/download/repo/%s/%s/srpms/" % tup
    ]

    if release == "stable":
        cmds.append("/usr/bin/rsync -rav --delete -e ssh tars/  %s@%s:/var/www/sites/virt-factory.et.redhat.com/download/src/" % (user,host))

    for cmd in cmds:
        print cmd
        os.system(cmd)

if __name__ == "__main__":
   if len(sys.argv) != 3:
      print "usage: push-it-all.py user release"
      print "     user    -- name of ssh user on HOST"
      print "     release -- stable or devel"
      sys.exit(1)

   push(sys.argv[1],HOST,DISTRO, sys.argv[2])

