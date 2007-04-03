#!/usr/bin/python

import getopt
import os
import sys

#HOST="et.redhat.com"
HOST="grimlock.devel.redhat.com"
try:
    USERNAME=os.getenv("USER")
except:
    USERNAME=None
    
DISTRO="fc6"
RELEASE="devel"
ARCH="i686"
PATH="/var/www/sites/virt-factory.et.redhat.com/download"
DRYRUN=False

def push(user,host, path, distro, release, arch, dryrun):
    if release != "stable" and release != "devel":
        raise RuntimeError, "release must be stable or devel"
    
    args = {'user':user,
            'host':host,
            'path':path,
            'distro':distro,
            'release':release,
            'arch':arch}

    cmds = [
            """/usr/bin/ssh %(user)s@%(host)s mkdir -p %(path)s/repo/%(distro)s/%(release)s/%(arch)s %(path)s/repo/%(distro)s/%(release)s/srpms""" % args,
            """/usr/bin/rsync -rav --delete -e ssh rpms/ %(user)s@%(host)s:/%(path)s/repo/%(distro)s/%(release)s/%(arch)s/""" % args,
            """/usr/bin/rsync -rav --delete -e ssh srpms/  %(user)s@%(host)s:%(path)s/repo/%(distro)s/%(release)s/srpms/""" % args
            ]
    
    if release == "stable":
        cmds.append("/usr/bin/rsync -rav --delete -e ssh tars/  %(user)s@%(host)s:%(path)s/src/" % args)

    for cmd in cmds:
        print cmd
        if not dryrun:
            os.system(cmd)

def showHelp():
    print "usage: push-it-all.py user release"
    print "     user    -- name of ssh user on HOST"
    print "     release -- stable or devel"

if __name__ == "__main__":

    username=USERNAME
    hostname=HOST
    distro=DISTRO
    release=RELEASE
    arch=ARCH
    path=PATH
    dryrun=DRYRUN
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hn",[
            "help",
            "hostname=",
            "user=",
            "path=",
            "release=",
            "distro=",
            "arch=",
            "dry-run"
            ])
    except getopt.error, e:
        print "Error parsing command list arguments: %s" % e
        sys.exit()

    for (opt, val) in opts:
        if opt in ["--hostname"]:
            hostname=val
        if opt in ["--user"]:
            username=val
        if opt in ["--path"]:
            path=val
        if opt in ["--release"]:
            release=val
        if opt in ["--distro"]:
            distro=val
        if opt in ["--arch"]:
            arch=val
        if opt in ["-h", "--help"]:
            showHelp()
        if opt in ["-n", "--dry-run"]:
            dryrun=True

    push(username, hostname, path, distro, release, arch, dryrun)

