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

from modules import task 
from modules import authentication
from modules import config
from modules import deployment
from modules import distribution
from modules import image
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

   def run(self):
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

       task_obj = task.Task()
       task_results = task_obj.list(None, {})
       tasks = task_results.data

       # not a lot of tasks, no need for db sort...
       def sorter(a,b):
           return cmp(a["time"], b["time"])

       tasks.sort(sorter,reverse=True)

       for item in tasks:
           item = task.TaskData.produce(item)
           op = item.operation

           task_lock = threading.Lock()
           context = TaskContext(self.logger, item, tasks, task_lock)

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

       task_results2 = task_obj.list(None, {})
       tasks = task_results2.data
       for item in tasks:
           if item["state"] == TASK_STATE_FINISHED:
               self.delete(None, item)
       
       if once:
           return


   def __log_exc(self):
      (t, v, tb) = sys.exc_info()
      self.logger.debug("Exception occured: %s" % t )
      self.logger.debug("Exception value: %s" % v)
      self.logger.debug("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))
     
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
       
        self.item.state = TASK_ITEM_RUNNING
        self.edit(None, self.context.item.to_datastruct())

    def set_finished(self):
        """
        Flag a task as not running in the database ... and log that too.
        """
        self.logger.debug("Finished task : %s" % self.item.id)
        self.item.state = TASK_ITEM_FINISHED
        self.edit(None, self.context.item.to_datastruct())
 
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
            self.__log_exc()
            self.tasklock.release()
            self.join()
 
        self.set_finished()
        self.tasklock.release()
        self.join()

#--------------------------------------------------------------------------

class CobblerInstallMetalThread(ShadowWorkerThread):

    """
    Background thread for installing a bare metal system.
    """

    def run(self, machine_id):
        # FIXME: make call to node to reprovision itself.
        # this does NOT need the lock.
        self.join()

#--------------------------------------------------------------------------

class CobblerInstallVirtThread(ShadowWorkerThread):

    """
    Background thread for installing a virtualized system.
    """

    def do_install_virt(self, deployment_id):
        # FIXME: make call to node to install virt image
        # this does NOT need the lock.
        self.join()

#--------------------------------------------------------------------------

class PuppetSyncThread(ShadowWorkerThread):

    """
    Background thread for updating the puppet config.
    """

    def do_puppet_sync(self):
        # update puppet mappings to match database

        self.tasklock.acquire()
        self.set_running()

        # FIXME: do puppet stuff here

        self.set_finished()
        self.tasklock.release()
        self.join()

#--------------------------------------------------------------------------
      
def main(argv):
    """
    Start things up.
    """
    
    scheduler = TaskScheduler()     

    if len(argv) > 1 and argv[1].lower() == "--serve":
        scheduler.run()
    elif len(argv) > 1 and argv[1].lower() == "--next":
        scheduler.tick()
    else:
        print "Usage:" 
        print "daemon mode:   taskatron.py --serve"
        print "debug:         taskatron.py --next"
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)


