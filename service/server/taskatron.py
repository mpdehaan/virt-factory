#!/usr/bin/python

"""
Laser Taskatron 3000
(aka Virt-factory-a-tron 3000 backend task scheduler code)

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


import os
import time
import string
import traceback
import threading
import sys
import glob
import socket

# import distutils.sysconfig
# sys.path.append("%s/virt-factory" % distutils.sysconfig.get_python_lib())

from codes import *
import config_data
import logger
# FIXME: pull this from the config file -akl
logger.logfilepath = "/var/lib/virt-factory/taskatron.log" # FIXME

print sys.path
from modules import task as task_module 
from modules import authentication
from modules import config
from modules import deployment
from modules import distribution
from modules import profile
from modules import machine
from modules import provisioning
from modules import registration
from modules import user

from M2Crypto import SSL
from M2Crypto.m2xmlrpclib import SSL_Transport, Server
from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

#--------------------------------------------------------------------------

class TaskScheduler:
   """
   Main class of the background scheduler daemon thingy (TM).
   """

   def __init__(self):
       """
       Constructify, with configs and log info.
       """

       if not os.path.exists(config_data.CONFIG_FILE):
           print "\nNo %s found.\n" % config_data.CONFIG_FILE
           return

       config_obj = config_data.Config()
       self.config = config_obj.get()
       # FIXME: use seperate log file (?)
       self.logger = logger.Logger().logger 
       self.pem_file = self.get_pem_file()

   def get_pem_file(self):
       # FIXME: there may some chance puppet would have multiple files
       # in this directory if there was more than one hostname.  Account
       # for that when the time comes.
       
       files = glob.glob("/var/lib/puppet/ssl/private_keys/*pem")
       if len(files) == 0:
           raise RuntimeError("no file in /var/lib/puppet/ssl/private_keys")
       return files[0]

   def clean_up_tasks(self):
       """
       If we start up and any tasks are marked as "running", this means
       taskatron died before they were finished.  Requeue them.
       """
       task_obj = task_module.Task()
       task_results = task_obj.list(None, {})
       tasks = task_results.data
       for task in tasks:
           item = task_module.TaskData.produce(task)
           if item.state == TASK_STATE_RUNNING:
               item.state = TASK_STATE_QUEUED
               print "queuing unfinished task: %s" % item.to_datastruct()
               task_obj.edit(None, item.to_datastruct())
         

   def run_forever(self, hostname):
       """
       Run forever.
       """
       while(True):
           self.tick(hostname, False)
           time.sleep(1)

   def tick(self,hostname,once=True):
       """
       The code for processing the queue.  If once, eat just
       one element, if not, process everything in the list.
       """

       now = time.time()

       task_obj = task_module.Task()
       task_results = task_obj.list(None, {})
       tasks = task_results.data

       # not a lot of tasks, no need for db sort...
       def sorter(a,b):
           return cmp(a["time"], b["time"])
       tasks.sort(sorter,reverse=True)

       # run any tasks in the queue.
       for item in tasks:
           print "---"
           print "taskatron considering: %s" % item
           item = task_module.TaskData.produce(item)
           op = item.action_type

           context = TaskContext(self.logger, item, tasks, hostname)

           print "state : %s" % item.state
           if item.state == TASK_STATE_QUEUED:
               if op == TASK_OPERATION_INSTALL_VIRT:
                   worker = InstallVirtThread(context)
               elif op == TASK_OPERATION_STOP_VIRT:
                   worker = StopVirtTaskThread(context)               
               elif op == TASK_OPERATION_START_VIRT:
                   worker = StartVirtThread(context)
               elif op == TASK_OPERATION_DELETE_VIRT:  
                   worker = DeleteVirtThread(context)
               else:
                   raise TaskException(comment="unknown task type")
               worker.run()

       task_results2 = task_obj.list(None, {})
       tasks = task_results2.data
       print "==="

       # keep finished tasks in the list for 30 minutes or so

       for item in tasks:
           if item["state"] == TASK_STATE_FINISHED and time.time() - now > 30*60:
               print "deleting: %s" % item
               task_obj.delete(None, item)
       
       if once:
           return


     
#-------------------------------------------------------------------------

class TaskContext:
    """
    State passed around to all worker threads when they are created.
    """

    def __init__(self, logger, item, items, hostname):
        self.logger = logger
        self.item = item
        self.items = items
        self.hostname = hostname

#-------------------------------------------------------------------------

class ShadowWorkerThread(threading.Thread):
    """
    Base class for all worker threads.
    """

    def __init__(self, context):
        """
        Constructify.
        """
        if context is not None:
            threading.Thread.__init__(self)
            self.logger   = context.logger
            self.item     = context.item
            self.items    = context.items
            self.hostname = context.hostname
        else:
            # FIXME: only for debug purposes, remove this line and the else.
            self.hostname = "mdehaan.rdu.redhat.com"

    def debug(self,str):
        self.logger.debug(str)
        print str

    def main_loop(self):
        return

    def set_running(self):
        """
        Flag a task as running in the database ... and log it.
        """
        self.debug("Running task  : %s" % self.item.id)
        self.debug("      action  : %s" % self.item.action_type)
        self.debug("     machine  : %s" % self.item.machine_id)
        self.debug("  deployment  : %s" % self.item.deployment_id)
        self.debug("        user  : %s" % self.item.user_id)
        self.debug("        time  : %s" % self.item.time)
        self.item.state = TASK_STATE_RUNNING
        task_obj = task_module.Task()
        task_obj.edit(None, self.item.to_datastruct())
         

    def set_finished(self):
        """
        Flag a task as not running in the database ... and log that too.
        """
        self.debug("Finished task : %s" % self.item.id)
        print "Finished task : %s" % self.item.id
        self.item.state = TASK_STATE_FINISHED
        task_obj = task_module.Task()
        task_obj.edit(None, self.item.to_datastruct())
        
    def set_failed(self):
        """
        Set a task as failed.
        """
        self.debug("Failing task : %s" % self.item.id)
        print "Failing task : %s" % self.item.id
        self.item_state = TASK_STATE_FAILED
        task_obj = task_module.Task()
        task_obj.edit(None, self.item.to_datastruct())

    def log_exc(self):
        """
        Log a stacktrace.
        """
        (t, v, tb) = sys.exc_info()
        self.debug("Exception occured: %s" % t )
        self.debug("Exception value: %s" % v)
        self.debug("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
 
    def run(self):
        """
        The loop for all threads only differs by self.core_fn(), which should be overridden.
        """
        try:
            self.set_running()
            # the failure mode here is that the node should always raise exceptions if an operation fails.
            self.core_fn()
            self.set_finished()
        except Exception, e:
            self.debug("*** THREAD FAILED ***")
            self.log_exc()
            self.set_failed()

    def get_records(self):
        """
        Helper function to retrieve objects and datastructures based on the machine and deployment info in the 
        task entry.
        """
        mid = self.item.machine_id
        did = self.item.deployment_id
        machine_obj = machine.Machine()
        deployment_obj = deployment.Deployment()
        machine_record = machine_obj.get(None, { "id" : mid })
        if not machine_record.ok():
            raise TaskException(comment="machine missing")
        if did >= 0:
            deployment_record = deployment_obj.get(None, { "id" : did })
            if not deployment_record.ok():
                raise TaskException(comment="deployment missing")
        else:
            deployment_record = None
        return (machine_obj, machine_record.data, deployment_obj, deployment_record.data)

    def callback(self, *args):
        print args
        return

    def get_handle(self,target,testmode=False):
        """
        Return a xmlrpc server object for a given hostname.
        """

        ctx = SSL.Context('sslv23')
        
        # Load CA cert
        ctx.load_client_ca("/var/lib/puppet/ssl/ca/ca_crt.pem")

        # Load target cert ...
        # FIXME: paths
        ctx.load_cert(
           certfile="/var/lib/puppet/ssl/certs/%s.pem" % self.hostname,
           keyfile="/var/lib/puppet/ssl/private_keys/%s.pem" % self.hostname
        )

        ctx.set_session_id_ctx('xmlrpcssl')

        ctx.set_info_callback(self.callback)
        uri = "https://%s:2112" % target
        print "contacting: %s" % uri
        rserver = Server(uri, SSL_Transport(ssl_context = ctx))
        return rserver 

#--------------------------------------------------------------------------
        
class InstallVirtThread(ShadowWorkerThread):

    """
    Background thread for installing a virtualized system.
    """
        
    def core_fn(self):
        (mrec, mdata, drec, ddata) = self.get_records()
        machine_hostname = mdata["hostname"]
        return self.get_handle(machine_hostname).install_virt(ddata)

#--------------------------------------------------------------------------

class DeleteVirtThread(ShadowWorkerThread):

    """
    Background thread for installing a virtualized system.
    """

    def core_fn(self):
        (mrec, mdata, drec, ddata) = self.get_records()
        machine_hostname = mdata["hostname"]
        return self.get_handle(machine_hostname).delete_virt(ddata)

#--------------------------------------------------------------------------

class StartVirtThread(ShadowWorkerThread):

    """
    Background thread for installing a virtualized system.
    """

    def core_fn(self):
        (mrec, mdata, drec, ddata) = self.get_records()
        machine_hostname = mdata["hostname"]
        return self.get_handle(machine_hostname).start_virt(ddata)

#--------------------------------------------------------------------------

class StopVirtThread(ShadowWorkerThread):

    """
    Background thread for updating the puppet config.
    """

    def core_fn(self):
        (mrec, mdata, drec, ddata) = self.get_records()
        machine_hostname = mdata["hostname"]
        # all of these fns should raise exceptions on failure.
        self.get_handle(machine_hostname).stop_virt(ddata)
        mrec.database_delete(mdata)
        return        

#--------------------------------------------------------------------------
      
def main(argv):
    """
    Start things up.
    """

    scheduler = TaskScheduler()     

    if len(sys.argv) > 2 and sys.argv[1].lower() == "--test":
        temp_obj = ShadowWorkerThread(None)
        handle = temp_obj.get_handle(sys.argv[2],True)
        print handle.test_add(1,2)
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "--daemon":
        scheduler.clean_up_tasks()
        scheduler.run_forever(socket.gethostname())
    elif len(sys.argv) == 0:
        print "Running single task in debug mode, since --daemon wasn't specified..."
        scheduler.clean_up_tasks()
        scheduler.tick(socket.gethostname(), True)
    else:
        print "Usage: "
        print "vf_taskatron --test server.fqdn"
        print "vf_taskatron --daemon"
        print "vf_tasktron  (no args) (just runs through one pass)"

if __name__ == "__main__":
    main(sys.argv)



