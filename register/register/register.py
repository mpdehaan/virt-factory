#!/usr/bin/python

"""
Virt-factory client code.

Copyright 2007, Red Hat, Inc
Adrian Likins <alikins@redhat.com>
Michael DeHaan <mdehaan@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import machine_info
import logger
logger.logfilepath = "/var/log/virt-factory-register/vf_register.log"

import getopt
import string
import sys
import socket
import os
import os.path
import traceback

from busrpc.rpc import lookup_service
from busrpc.crypto import CertManager
import busrpc.qpid_transport

from rhpl.translate import _, N_, textdomain, utf8
I18N_DOMAIN = "vf_registerr"
ERR_TOKEN_INVALID = 2   # from codes.py, which we don't import because it's not installed ??
ERR_ARGUMENTS_INVALID = 8 # ...

class Server:
    def __init__(self, host=None):
        transport = busrpc.qpid_transport.QpidTransport()
        transport.connect()

        cm = CertManager('/var/lib/virt-factory/qpidcert', host)
    
        self.rpc_interface = lookup_service("rpc", transport, host=host, cert_mgr=cm)
        if self.rpc_interface == None:
            print "Lookup failed :("
            sys.exit(-1)    

    def __getattr__(self, name):
        return self.rpc_interface.__getattr__(name)


class Register(object):
    def __init__(self,url):
        self.server_url = url
        self.server_host = self.server_url.split('/')[2]
        self.server_host = self.server_host.split(':')[0]
        self.logger = logger.Logger().logger
        self.server = Server(self.server_host)
        self.token = None

    # assume username/password exist, so no user creation race conditions to avoid
    # like RHN
    def login(self, username, password):
        if not self.token:
            self.token = self.server.user_login(username, password)[1]['data']
    
    def register(self, hostname, ip, mac, profile_name, virtual):
        # should return a machine_id, maybe more
        self.logger.info("--------------------")
        self.logger.info("Registering...")
        self.logger.info("  token=%s" % self.token)
        self.logger.info("  hostname=%s" % hostname)
        self.logger.info("  ip=%s" % ip)
        self.logger.info("  mac=%s" % mac)
        self.logger.info("  profile_name=%s" % profile_name)
        self.logger.info("  virtual=%s" % virtual)
        self.logger.info("---------------------")
        if profile_name is None:
            profile_name = ""
        if mac is None:
            mac = "00:00:00:00:00:00"
        try:
            rc = self.server.register(self.token, hostname, ip, mac, profile_name, virtual)
        except TypeError:
            (t, v, tb) = sys.exc_info()
            self.logger.error("error running registration.")
            self.logger.debug("Exception occured: %s" % t )
            self.logger.debug("Exception value: %s" % v)
            self.logger.error("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
            sys.exit(1)
        if rc[0] == 0:
            self.logger.info("Registration succeeded.")
            fd1 = open("/etc/sysconfig/virt-factory/token","w+")
            fd1.write(self.token)
            fd1.close()
            fd2 = open("/etc/sysconfig/virt-factory/server","w+")
            fd2.write(self.server_url)
            fd2.close()
            fd3 = open("/etc/sysconfig/virt-factory/mac", "w+")
            fd3.write(mac)
            fd3.close()
            fd4 = open("/etc/sysconfig/virt-factory/profile", "w+")
            fd4.write(profile_name)
            fd4.close()
            self.update_puppet_sysconfig(self.server_host)
            puppetcmd = "/usr/sbin/puppetd --waitforcert 0 --server " + self.server_host + " --certname " + hostname + " --test"
            self.logger.info("puppet cmd: %s" % puppetcmd)
            puppet_in, puppet_out = os.popen4(puppetcmd)
            for line in puppet_out.readlines():
                self.logger.info("puppet: %s" % line.strip())
            puppet_in.close()
            puppet_out.close()

            rc2 = self.server.sign_node_cert(self.token, hostname)
            if rc2[0] != 0:
                self.logger.error("Failed: %s" % rc2)
                rc = rc2
            
        else:
            self.logger.info("Failed: %s" % rc)
        return rc

    def update_puppet_sysconfig(self, server):
        file = open("/etc/sysconfig/puppet","w+")
        file.write("PUPPET_SERVER=%s\n" % server)
        file.close()

    def register_system(self, regtoken, username, password, profile_name, virtual):
        if regtoken:
            self.token = regtoken
        else:
            self.login(username, password)

        net_info = machine_info.get_netinfo(self.server_url)
        self.logger.info(net_info)
 
        try:
            rc = self.register(net_info['hostname'], net_info['ipaddr'], net_info['hwaddr'], profile_name, virtual)
        except socket.error:
            print _("Could not connect to server.")
            return 1
        if rc[0] == ERR_TOKEN_INVALID:
            self.logger.info("Bad token!  No registration for you!")
        elif rc[0] == ERR_ARGUMENTS_INVALID:
            self.logger.info("Invalid arguments.  Possibly missing --profilename ?")
        elif rc[0] != 0:
            self.logger.info("There was an error.  Check the server side logs.")
        else:
            # it's all good
            cmdline = " ".join(sys.argv[1:])
            fd5 = open("/etc/sysconfig/virt-factory/register","w+")
            fd5.write(cmdline)
            fd5.close()
        return rc[0]

def showHelp():
    print "register [--help] [--token] [--serverurl=]"


def main(argv):

    regtoken   = "UNSET"
    username   = None
    password   = None
    server_url = None
    profile_name = ""
    virtual      = False

    # ensure we have somewhere to save parameters to, the node daemon will want
    # to know them later.

    if not os.path.exists("/etc/sysconfig/virt-factory"):
        os.makedirs("/etc/sysconfig/virt-factory")

    try:
        opts, args = getopt.getopt(argv[1:], "ht:u:p:s:P:v", [
            "help", 
            "token=", 
            "username=",
            "password=", 
            "serverurl=",
            "profilename=",
            "virtual"
        ])
    except getopt.error, e:
        print _("Error parsing command list arguments: %s") % e
        showHelp()
        sys.exit(1)

    for (opt, val) in opts:
        #print "DEBUG: this (%s,%s)" % (opt,val)
        if opt in ["-h", "--help"]:
            showHelp()
            sys.exit(1)
        if opt in ["-t", "--token"]:
            regtoken = val
        if opt in ["-u", "--username"]:
            username = val
        if opt in ["-p", "--password"]:
            password = val
        if opt in ["-s", "--serverurl"]:
            server_url = val
        if opt in ["-i", "--profilename"]:
            #print "read the profile name"
            profile_name = val
        if opt in ["-v", "--virtual"]:
            virtual = True

    if server_url is None:
        print _("must specify --serverurl, ex: http://foo.example.com:5150")
        sys.exit(1)
    
    if regtoken is None:
        if username is None:
           print _("must specify --token or --username and --password")
           sys.exit(1)
        elif password is None:
           print _("must specify --password")
           sys.exit(1)        

    reg_obj = Register(server_url)
    return_status = reg_obj.register_system(regtoken, username, password, profile_name, virtual)
    sys.exit(return_status)


if __name__ == "__main__":
    textdomain(I18N_DOMAIN)
    main(sys.argv)



