"""
Laser Taskatron 3000
(aka ShadowManager backend task scheduler code)

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


import os
import time
import string
import traceback
import threading
import sys

from codes import *
import config_data
import logger
logger.logfilepath = "/var/lib/shadowmanager/taskatron.log" # FIXME

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

PEM_ROOT = "/var/lib/puppet/ssl/ca/signed"

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
         

   def run_forever(self):
       """
       Run forever.
       """
       while(True):
           self.tick(False)
           time.sleep(1)

   def tick(self,once=True):
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
           op = item.operation

           context = TaskContext(self.logger, item, tasks, task_lock)

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
               worker.consider()

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

    def __init__(self, logger, item, items, tasklock):
        self.logger = logger
        self.item = item
        self.items = items
        self.tasklock = tasklock

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

    def main_loop(self):
        return

    def set_running(self):
        """
        Flag a task as running in the database ... and log it.
        """
        self.logger.debug("Running task  : %s" % self.item.id)
        self.logger.debug("   operation  : %s" % self.item.operation)
        self.logger.debug("  parameters  : %s" % self.item.parameters)
        print "Running task  : %s" % self.item.id
        print "   operation  : %s" % self.item.operation
        print "  parameters  : %s" % self.item.parameters
       
        self.item.state = TASK_ITEM_RUNNING
        task_obj = task_module.Task()
        task_obj.edit(None, self.item.to_datastruct())
         

    def set_finished(self):
        """
        Flag a task as not running in the database ... and log that too.
        """
        self.logger.debug("Finished task : %s" % self.item.id)
        print "Finished task : %s" % self.item.id
        self.item.state = TASK_STATE_FINISHED
        task_obj = task_module.Task()
        task_obj.edit(None, self.item.to_datastruct())
        
    def set_failed(self):
        """
        Set a task as failed.
        """
        self.logger.debug("Failing task : %s" % self.item.id)
        print "Failing task : %s" % self.item.id
        self.item_state = TASK_STATE_FAILED
        task_obj = task_module.Task()
        task_obj.edit(None, self.item.to_datastruct())

    def log_exc(self):
        """
        Log a stacktrace.
        """
        (t, v, tb) = sys.exc_info()
        self.logger.debug("Exception occured: %s" % t )
        self.logger.debug("Exception value: %s" % v)
        self.logger.debug("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
 
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
            self.log_exc()
            self.set_failed()

    def get_virt_records(self):
        """
        Helper function to retrieve objects and datastructures based on the machine and deployment info in the 
        task entry.
        """
        mid = self.item.machine_id
        did = self.item.deployment_id
        machine_obj = machine.Machine()
        deployment_obj = deployment.Deployment()
        machine_record = machine_obj.get(None, { "id" : mid })
        deployment_record = deployment_obj.get(none, { "id" : did })
        if not machine_obj.ok():
            raise TaskException(comment="machine missing")
        if not deployment_obj.ok():
            raise TaskException(comment="deployment missing")
        return (machine_obj, machine_record.data, deployment_obj, deployment_record.data)

    def callback(self, *args):
        print args
        return

    def get_handle(self,hostname,testmode=False):
        """
        Return a xmlrpc server object for a given hostname.
        """

        pem_file = os.path.join(PEM_ROOT, "%s.pem" % hostname)
        if testmode:
            print "pem_file", pem_file

        ctx = SSL.Context('sslv23')
        ctx.load_cert(pem_file)
        ctx.load_client_ca(pem_file)
        ctx.load_verify_info(pem_file)
        ctx.set_session_id_ctx('xmlrpcssl')

        ctx.set_info_callback(self.callback)
        address = (hostname, 2112)
        rserver = xmlrpcserver(ctx, address)
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

    # def get_handle(self,hostname):
    if len(sys.argv) > 1 and sys.argv[1].lower() == "test":
        temp_obj = ShadowWorkerThread(None)
        handle = temp_obj.get_handle("mdehaan.rdu.redhat.com",True)
        print t.test()
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "--daemon":
        scheduler.clean_up_tasks()
        scheduler.run_forever()
    else:
        print "Running single task in debug mode, since --daemon wasn't specified..."
        scheduler.tick()

if __name__ == "__main__":
    main(sys.argv)



