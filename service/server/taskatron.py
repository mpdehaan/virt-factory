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
import sys
import glob
import socket
import socket
import subprocess

# import distutils.sysconfig
# sys.path.append("%s/virt-factory" % distutils.sysconfig.get_python_lib())

from codes import *
import config_data
import logger
import utils
# FIXME: pull this from the config file -akl
logger.logfilepath = "/var/lib/virt-factory/taskatron.log" # FIXME

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

#from M2Crypto import SSL
#from M2Crypto.m2xmlrpclib import SSL_Transport, Server
#from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

#--------------------------------------------------------------------------

class Taskatron:
    def __init__(self):
        """
        Constructor sets up logging
        """
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
                self.logger.info("queuing unfinished task: %s" % item.to_datastruct())
                task_obj.edit(None, item.to_datastruct())
         

    def run_forever(self):
        """
        Run forever.
        """
        me = socket.gethostname()
        while(True):
            self.dotick(me)
            time.sleep(1)

    def dotick(self,hostname,once=False):
        """
        The code for processing the queue.  If once, eat just
        one element, if not, process everything in the list.
        """

        now = time.time()

        task_obj = task_module.Task()
        task_results = task_obj.list(None, {})
        tasks = task_results.data

        task_results = task_obj.list(None, {})
        tasks = task_results.data

        # not a lot of tasks, no need for db sort...
        def sorter(a,b):
            return cmp(a["time"], b["time"])
        tasks.sort(sorter,reverse=True)

        # run any tasks in the queue.
        for item in tasks:
            item = task_module.TaskData.produce(item)
            op = item.action_type

            if item.state == TASK_STATE_QUEUED:
                self.logger.info("*** RUNNING")
                task = item
                self.set_running(task)
                try:
                    rc = 0
                    self.logger.info("operation : %s" % op)
                    if op == TASK_OPERATION_INSTALL_VIRT:
                        rc = self.install_virt(task)
                    elif op == TASK_OPERATION_SHUTDOWN_VIRT:
                        rc = self.shutdown_virt(task)
                    elif op == TASK_OPERATION_START_VIRT:
                        rc = self.start_virt(task)
                    elif op == TASK_OPERATION_DELETE_VIRT:  
                        rc = self.delete_virt(task)
                    elif op == TASK_OPERATION_PAUSE_VIRT:  
                        rc = self.pause_virt(task)
                    elif op == TASK_OPERATION_UNPAUSE_VIRT:  
                        rc = self.unpause_virt(task)
                    elif op == TASK_OPERATION_DESTROY_VIRT:  
                        rc = self.destroy_virt(task)
                    else:
                        raise TaskException(comment="unknown task type")
                    self.logger.info(rc)
                    self.logger.info("setting finished")
                    if rc == 0:
                        self.set_finished(task)
                    else:
                        self.set_failed(task)
                except Exception, tb: 
                    self.logger.error("Exception:\n")
                    #self.logger.error(str(traceback.extract_tb(tb)))
                    traceback.print_exc() # until logging gets cleaned up
                    self.logger.error("setting failed")
                    self.set_failed(task)

        task_results2 = task_obj.list(None, {})
        tasks = task_results2.data

        # keep finished tasks in the list for 30 minutes or so
  
        if once:
            return


        # this is only temporary code to control the task list.
        # refine later.

        for item in tasks:

            # delete failed or finished records in 30 minutes

            if (item["state"] == TASK_STATE_FINISHED or item["state"] == TASK_STATE_FAILED) and time.time() - now > 30*60:
                self.logger.info("deleting: %s" % item)
                task_obj.delete(None, item)

     
    def set_running(self,task):
        """
        Flag a task as running in the database ... and log it.
        """
        #debug("Running task  : %s" % task.id)
        #debug("      action  : %s" % task.action_type)
        #debug("     machine  : %s" % task.machine_id)
        #debug("  deployment  : %s" % task.deployment_id)
        #debug("        user  : %s" % task.user_id)
        #debug("        time  : %s" % task.time)
        task.state = TASK_STATE_RUNNING
        task_obj = task_module.Task()
        task_obj.edit(None, task.to_datastruct())
       
    def set_finished(self,task):
        task.state = TASK_STATE_FINISHED
        task_obj = task_module.Task()
        task_obj.edit(None, task.to_datastruct())

    def set_failed(self,task):
        """
        Set a task as failed.
        """
        #debug("Failing task : %s" % task)
        task.state = TASK_STATE_FAILED
        task_obj = task_module.Task()
        task_obj.edit(None, task.to_datastruct())


    def get_records(self,task):
        """
        Helper function to retrieve objects and datastructures based on the machine and deployment info in the 
        task entry.
        """
        mid = task.machine_id
        did = task.deployment_id
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

    def callback(self,*args):
        print args
        return

    def node_comm(self,machine_hostname, command, *cmd_args):
        myhost = socket.gethostname() # FIXME
        args = [
            "/usr/bin/vf_nodecomm",
            myhost,
            machine_hostname,
            command
            ]
        for x in cmd_args:
            args.append(str(x))
        self.logger.info("args = ", args)
        rc =  subprocess.call(args)
        self.logger.info(rc)
        if rc != 0:
            raise UncaughtException(comment="failed")
        return (rc, 0)
       
    def install_virt(self,task):

        (mrec, mdata, drec, ddata) = self.get_records(task)
        machine_hostname = mdata["hostname"]
        self.logger.info("hostname target is ... (%s)" % machine_hostname)
        self.logger.info("go go gadget virt install!")
        (rc, data) = self.node_comm(machine_hostname, "virt_install", ddata["mac_address"], True)
        return rc


    def delete_virt(self,task):

        (mrec, mdata, drec, ddata) = self.get_records(task)
        machine_hostname = mdata["hostname"]
        (rc, data) =  self.node_comm(machine_hostname, "virt_delete", ddata["mac_address"])
        return rc

    def start_virt(self,task):

        (mrec, mdata, drec, ddata) = self.get_records(task)
        machine_hostname = mdata["hostname"]
        (rc, data) = self.node_comm(machine_hostname, "virt_start", ddata["mac_address"])
        return rc

    def stop_virt(self,task):

        (mrec, mdata, drec, ddata) = self.get_records(task)
        machine_hostname = mdata["hostname"]
        (rc, data) = self.node_comm(machine_hostname, "virt_stop", ddata["mac_address"])
        if rc == 0:
            mrec.set_state(DEPLOYMENT_STATE_STOPPED)
        return rc

    def pause_virt(self,task):

        (mrec, mdata, drec, ddata) = self.get_records(task)
        machine_hostname = mdata["hostname"]
        (rc, data) = self.node_comm(machine_hostname,"virt_pause",ddata["mac_address"])
        if rc == 0:
            drec.set_state(DEPLOYMENT_STATE_PAUSED)
        return rc

    def shutdown_virt(self,task):

        (mrec, mdata, drec, ddata) = self.get_records(task)
        machine_hostname = mdata["hostname"]
        (rc, data) = self.node_comm(machine_hostname, "virt_shutdown", ddata["mac_address"])
        if rc == 0:
            drec.set_state(DEPLOYMENT_STATE_STOPPED)
        return rc

    def destroy_virt(self,task):

        (mrec, mdata, drec, ddata) = self.get_records(task)
        machine_hostname = mdata["hostname"]
        (rc, data) = self.node_comm(machine_hostname, "virt_destroy", ddata["mac_address"])
        if rc == 0:
            drec.set_state(DEPLOYMENT_STATE_STOPPED)
        return rc


    def unpause_virt(self,task):

        (mrec, mdata, drec, ddata) = self.get_records(task)
        machine_hostname = mdata["hostname"]
        (rc, data) = self.node_comm(machine_hostname, "virt_unpause", ddata["mac_address"])
        if rc == 0:
            drec.set_state(DEPLOYMENT_STATE_RUNNING)
        return rc


#--------------------------------------------------------------------------
#--------------------------------------------------------------------------

def main(argv):
    """
    Start things up.
    """

    taskatron = Taskatron()
    if len(sys.argv) > 2 and sys.argv[1].lower() == "--test":
        print taskatron.node_comm(sys.argv[2],"test_add",1,2)
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "--daemon":
        taskatron.clean_up_tasks()
        utils.daemonize("/var/run/vf_taskatron.pid")
        taskatron.run_forever()
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "--infinity":
        taskatron.clean_up_tasks()
        taskatron.run_forever()
    elif len(sys.argv) == 1:
        print "Running single task in debug mode, since --daemon wasn't specified..."
        taskatron.clean_up_tasks()
        taskatron.dotick(socket.gethostname(), True)
    else:
        print "Usage: "
        print "vf_taskatron --test server.fqdn"
        print "vf_taskatron --daemon"
        print "vf_tasktron  (no args) (just runs through one pass)"

if __name__ == "__main__":
    main(sys.argv)


