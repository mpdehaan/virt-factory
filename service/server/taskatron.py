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

import db
from codes import *
import config_data
import logger
import utils

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

from rhpl.translate import _, N_, textdomain, utf8
I18N_DOMAIN = "vf_server"

#--------------------------------------------------------------------------

class Taskatron:
    def __init__(self):
        """
        Constructor sets up logging
        """
        self.logger = logger.Logger(logfilepath = "/var/log/virt-factory/taskatron.log").logger
        self.session = db.open_session()

    def __log_exc(self):
        (t, v, tb) = sys.exc_info()
        self.logger.info("Exception occured: %s" % t )
        self.logger.info("Exception value: %s" % v)
        self.logger.info("Exception Info:\n%s" % string.join(traceback.format_list(traceback.extract_tb(tb))))


    def clean_up_tasks(self):
        """
        If we start up and any tasks are marked as "running", this means
        taskatron died before they were finished.  Requeue them.
        """
        task_obj = task_module.Task()
        task_results = task_obj.list(None, {})
        tasks = task_results.data

        for task in tasks:
            item = db.Task.get(self.session, task["id"])
            if item.id is None:
                item.id = -1   
            if item.state == TASK_STATE_RUNNING:
                item.state = TASK_STATE_QUEUED
                self.logger.info("queuing unfinished task: %s" % task)
                self.session.save(item)
                self.session.flush()
         

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

        # not a lot of tasks, no need for db sort...
        def sorter(a,b):
            return cmp(a["time"], b["time"])
        tasks.sort(sorter,reverse=True)

        # run any tasks in the queue.
        for task in tasks:
            item = db.Task.get(self.session, task["id"])
            op = item.action_type

            if item.user_id is None:
                item.user_id = -1

            if item.state == TASK_STATE_QUEUED:
                self.logger.info("*** RUNNING")
                task = item
                self.set_running(item)
                try:
                    rc = 0
                    self.logger.info("operation : %s" % op)
                    if op == TASK_OPERATION_INSTALL_VIRT:
                        rc = self.install_virt(item)
                    elif op == TASK_OPERATION_SHUTDOWN_VIRT:
                        rc = self.shutdown_virt(item)
                    elif op == TASK_OPERATION_START_VIRT:
                        rc = self.start_virt(item)
                    elif op == TASK_OPERATION_DELETE_VIRT:  
                        rc = self.delete_virt(item)
                    elif op == TASK_OPERATION_PAUSE_VIRT:  
                        rc = self.pause_virt(item)
                    elif op == TASK_OPERATION_UNPAUSE_VIRT:  
                        rc = self.unpause_virt(item)
                    elif op == TASK_OPERATION_DESTROY_VIRT:  
                        rc = self.destroy_virt(item)
                    elif op == TASK_OPERATION_TEST:
                        rc = self.test(item)
                    else:
                        raise TaskException(comment="unknown task type")
                    self.logger.info(rc)
                    self.logger.info("setting finished")
                    if rc == 0:
                        self.set_finished(item)
                    else:
                        self.set_failed(item)
                except Exception, tb: 
                    self.logger.error("Exception:\n")
                    #self.logger.error(str(traceback.extract_tb(tb)))
                    #traceback.print_exc() # until logging gets cleaned up
                    self.__log_exc()
                    self.logger.error("setting failed")
                    self.set_failed(item)

        task_results2 = task_obj.list(None, {})
        tasks = task_results2.data

        # keep finished tasks in the list for 30 minutes or so
  
        if once:
            return


        # this is only temporary code to control the task list.
        # refine later.

        for task in tasks:

            # delete failed or finished records in 30 minutes
            item = db.Machine.get(self.session, task["id"])

            if (item.state == TASK_STATE_FINISHED or item.state == TASK_STATE_FAILED) and time.time() - now > 30*60:
                self.logger.info("deleting: %s" % item)
                db.Machine.delete(self.session, task["id"])
                self.session.save()
                self.session.flush()
     
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
        task = db.Task.get(self.session, task.id)
        task.state = TASK_STATE_RUNNING
        self.session.save(task)
        self.session.flush()
       
    def set_finished(self,task):
        task = db.Task.get(self.session, task.id)
        task.state = TASK_STATE_FINISHED
        self.session.save(task)
        self.session.flush()

    def set_failed(self,task):
        """
        Set a task as failed.
        """
        #debug("Failing task : %s" % task)
        task = db.Task(self.session, task.id)
        task.state = TASK_STATE_FAILED
        self.session.save(task)
        self.session.flush()


    def get_records(self,task):
        """
        Helper function to retrieve objects and datastructures based on the machine and deployment info in the 
        task entry.
        """
        mid = task["machine_id"]
        did = task["deployment_id"]

        machine_record = db.Machine.get(self.session, mid)

        if not machine_record:
            raise TaskException(comment="machine missing")
        if did >= 0:
            deployment_record = db.Deployment.get(self.session, did)
            if not deployment_record:
                raise TaskException(comment="deployment missing")
            ddata = deployment_record.expand()
        else:
            raise TaskException(comment="deployment missing")
        return (machine_record, deployment_record)

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

        (mdata, ddata) = self.get_records(task)
        self.logger.info("hostname target is ... (%s)" % mdata.machine_hostname)
        self.logger.info("go go gadget virt install!")
        (rc, data) = self.node_comm(machine_hostname, "virt_install", ddata.mac_address, True)
        return rc


    def delete_virt(self,task):

        (mdata, ddata) = self.get_records(task)
        machine_hostname = mdata.hostname
        (rc, data) =  self.node_comm(machine_hostname, "virt_delete", ddata.mac_address)
        return rc

    def start_virt(self,task):

        (mdata, ddata) = self.get_records(task)
        machine_hostname = mdata.hostname
        (rc, data) = self.node_comm(machine_hostname, "virt_start", ddata.mac_address)
        return rc

    def stop_virt(self,task):

        (mdata, ddata) = self.get_records(task)
        machine_hostname = mdata.mac_address
        (rc, data) = self.node_comm(machine_hostname, "virt_stop", ddata.mac_address)
        if rc == 0:
            mdata.state = DEPLOYMENT_STATE_STOPPED
            self.session.save(mdata)
            self.session.flush()
        return rc

    def pause_virt(self,task):

        (mdata, ddata) = self.get_records(task)
        machine_hostname = mdata.hostname
        (rc, data) = self.node_comm(machine_hostname,"virt_pause",ddata.mac_address)
        if rc == 0:
            ddata.state = DEPLOYMENT_STATE_PAUSED
            self.session.save(ddata)
            self.session.flush()

        return rc

    def shutdown_virt(self,task):

        (mdata, ddata) = self.get_records(task)
        machine_hostname = mdata.hostname
        (rc, data) = self.node_comm(machine_hostname, "virt_shutdown", ddata.mac_address)
        if rc == 0:
            ddata.state = DEPLOYMENT_STATE_STOPPED
            self.session.save(ddata)
            self.session.flush()
        return rc

    def destroy_virt(self,task):

        (mdata, ddata) = self.get_records(task)
        machine_hostname = mdata.hostname
        (rc, data) = self.node_comm(machine_hostname, "virt_destroy", ddata.mac_address)
        if rc == 0:
            ddata.state = DEPLOYMENT_STATE_STOPPED
            self.session.save(ddata)
            self.session.flush()
        return rc

    def test(self, task):
        
        (mdata, ddata) = self.get_records(task)
        machine_hostname = mdata.hostname
        (rc, data) = self.node_comm(machine_hostname, "test_blippy", 52.8)
        return rc

    def unpause_virt(self,task):

        (mdata, ddata) = self.get_records(task)
        machine_hostname = mdata.hostname
        (rc, data) = self.node_comm(machine_hostname, "virt_unpause", ddata.mac_address)
        if rc == 0:
            ddata.state = DEPLOYMENT_STATE_RUNNING
            self.session.save(ddata)
            self.ession.flush()
        return rc

#--------------------------------------------------------------------------

def main(argv):
    """
    Start things up.
    """
    config_obj = config_data.Config()
    config = config_obj.get()
    databases = config['databases']
    url = databases['primary']
    # connect
    db.Database(url)

    textdomain(I18N_DOMAIN)
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
        print _("Running single task in debug mode, since --daemon wasn't specified...")
        taskatron.clean_up_tasks()
        taskatron.dotick(socket.gethostname(), True)
    else:
        useage = _("""Usage:
vf_taskatron --test server.fqdn
vf_taskatron --daemon
vf_tasktron  (no args) (just runs through one pass)
""")
        print useage
            

if __name__ == "__main__":
    main(sys.argv)


