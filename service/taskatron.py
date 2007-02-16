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

from codes import *
import config_data
import logger

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
       taskatron died before they were finished.  Should they be marked
       finished/stopped or queued?
       FIXME: figure this out.
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

       task_obj = task_module.Task()
       task_results = task_obj.list(None, {})
       tasks = task_results.data

       # not a lot of tasks, no need for db sort...
       def sorter(a,b):
           return cmp(a["time"], b["time"])

       tasks.sort(sorter,reverse=True)

       for item in tasks:
           print "---"
           print "taskatron considering: %s" % item
           item = task_module.TaskData.produce(item)
           op = item.operation

           task_lock = threading.Lock()
           context = TaskContext(self.logger, item, tasks, task_lock)

           print "state : %s" % item.state
           if item.state == TASK_STATE_QUEUED:
               if op == TASK_OPERATION_COBBLER_SYNC:
                   worker = CobblerSyncThread(context)
               elif op == TASK_OPERATION_INSTALL_METAL:
                   worker = CobblerInstallMetalThread(context)
               elif op == TASK_OPERATION_INSTALL_VIRT:
                   worker = CobblerInstallVirtThread(context)
               elif op == TASK_OPERATION_PUPPET_SYNC:
                   worker = PuppetSyncThread(context)
               else:
                   raise TaskException(comment="unknown task type")
               worker.start()

       task_results2 = task_obj.list(None, {})
       tasks = task_results2.data
       print "==="
       for item in tasks:
           if item["state"] == TASK_STATE_FINISHED:
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
        threading.Thread.__init__(self)
        self.logger   = context.logger
        self.item     = context.item
        self.items    = context.items
        self.tasklock = context.tasklock

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

    def log_exc(self):
        (t, v, tb) = sys.exc_info()
        self.logger.debug("Exception occured: %s" % t )
        self.logger.debug("Exception value: %s" % v)
        self.logger.debug("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
 
#--------------------------------------------------------------------------

class CobblerSyncThread(ShadowWorkerThread):

    """
    Background thread for updating the cobbler config and tree.
    """   

    def run(self):

        # can't run this at the same time as other tasks...
        # FIXME: also can't run while any systems are in the
        # "provisioning" state... need to implement this.

        self.tasklock.acquire()
        try:
            self.set_running()
            prov_obj = provisioning.Provisioning()
            prov_obj.sync(None, {})
        except Exception, e:
            self.log_exc()
            self.tasklock.release()
        self.set_finished()
        self.tasklock.release()

#--------------------------------------------------------------------------

class CobblerInstallMetalThread(ShadowWorkerThread):

    """
    Background thread for installing a bare metal system.
    """

    def run(self):
        # FIXME: make call to node to reprovision itself.
        # this does NOT need the lock.
        #self.tasklock.acquire()
        try:
            self.set_running()
            # FIXME: do stuff here
        except Exception, e:
            self.log_exc()
            #self.tasklock.release()
        self.set_finished()
        #self.tasklock.release()

#--------------------------------------------------------------------------

#--------------------------------------------------------------------------

class CobblerInstallVirtThread(ShadowWorkerThread):

    """
    Background thread for installing a virtualized system.
    """

    def run(self):
        # FIXME: make call to node to install virt profile
        # this does NOT need the lock.
        #self.tasklock.acquire()
        try:
            self.set_running()
            # FIXME: do stuff here
        except Exception, e:
            self.log_exc()
            #self.tasklock.release()
        self.set_finished()
        #self.tasklock.release()


#--------------------------------------------------------------------------

class PuppetSyncThread(ShadowWorkerThread):

    """
    Background thread for updating the puppet config.
    """

    def run(self):
        # update puppet mappings to match database
        #self.tasklock.acquire()
        try:
            self.set_running()
            # FIXME: do stuff here
        except Exception, e:
            self.log_exc()
            #self.tasklock.release()
        self.set_finished()
        #self.tasklock.release()


#--------------------------------------------------------------------------
      
def main(argv):
    """
    Start things up.
    """
    
    scheduler = TaskScheduler()     

    if len(argv) > 1 and argv[1].lower() == "--serve":
        scheduler.clean_up_tasks()
        scheduler.run_forever()
    elif len(argv) > 1 and argv[1].lower() == "--next":
        scheduler.tick()
    else:
        print "Usage:" 
        print "daemon mode:   taskatron.py --serve"
        print "debug:         taskatron.py --next"
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)


