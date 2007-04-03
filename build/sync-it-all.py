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

repo_template="""
[%(repo_name)s]
name=%(repo_long_name)s
baseurl=%(base_url)s
enabled=%(enabled)s
gpgcheck=0
keepcache=0
"""
#"

DISTRO="fc6"
RELEASE="devel"
ARCH="i686"
PATH="/var/www/sites/virt-factory.et.redhat.com/download"
DRYRUN=False
URLPATH="download/"


def create_repo_d_file(repo, hostname, urlpath, release):
    repo_txt = repo_template % {'repo_name':"test_repo_%s" % repo,
                                'repo_long_name': "Test Repo for %s" % release,
                                'base_url': "http://%s/%s/repo/$releasever/%s/$basearch/" % (hostname, urlpath, release),                                
                                'enabled': "1"}
    if repo == "srpms":
        repo_text = repo_template % {'repo_name':"test_repo_%s" % repo,
                                     'repo_long_name': "Test Repo for %s" % release,
                                     'base_url': "http://%s/%s/repo/$releasever/%s/$repo/" % (hostname, urlpath, repo),                                
                                     'enabled': "1"}

    if not os.access("repos.d", os.W_OK):
        os.mkdir("repos.d")
        
    f = open("repos.d/test_repo_%s.repo" % repo, "w+")
    f.write(repo_txt)
    f.close()

def push(user, host, path, distro, release, arch, urlpath, dryrun):
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

    for repo in [arch, "srpms"]:
        create_repo_d_file(repo, hostname, urlpath, release)

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
    urlpath=URLPATH
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hn",[
            "help",
            "hostname=",
            "user=",
            "path=",
            "release=",
            "distro=",
            "arch=",
            "urlpath=",
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
        if opt in ["--urlpath"]:
            urlpath=val

    push(username, hostname, path, distro, release, arch, urlpath, dryrun)

