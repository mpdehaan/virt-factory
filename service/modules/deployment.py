#!/usr/bin/python

## Virt-factory backend code.
##
## Copyright 2006, Red Hat, Inc
## Michael DeHaan <mdehaan@redhat.com>
## Scott Seago <sseago@redhat.com>
## Adrian Likins <alikins@redhat.com>
##
## This software may be freely redistributed under the terms of the GNU
## general public license.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


from server.codes import *
from fieldvalidator import FieldValidator

import profile
import machine
import web_svc
import task
import regtoken
import provisioning
from server import config_data

import subprocess
import socket
import traceback
import threading


class Deployment(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"deployment_add": self.add,
                        "deployment_edit": self.edit,
                        "deployment_pause": self.pause,
                        "deployment_unpause": self.unpause,
                        "deployment_start": self.start,
                        "deployment_stop": self.shutdown,
                        "deployment_shutdown": self.shutdown,
                        "deployment_destroy": self.destroy,
                        "deployment_refresh": self.refresh,
                        "deployment_delete": self.delete,
                        "deployment_list": self.list,
                        "deployment_get": self.get}

        web_svc.AuthWebSvc.__init__(self)


    def associate(self, token, machine_id, hostname, ip_addr, mac_addr, profile_id=None,
              architecture=None, processor_speed=None, processor_count=None,
              memory=None):
        """
        Associate a machine with an ip/host/mac address
        """
        self.logger.info("associating...")
        # determine the profile from the token.
        # FIXME: inefficient. ideally we'd have a retoken.get_by_value() or equivalent
        regtoken_obj = regtoken.RegToken()
        if token is None:
            self.logger.info("token is None???")
        results = regtoken_obj.get_by_token(None, { "token" : token })
        self.logger.info("get_by_token")
        self.logger.info("results: %s" % results)
        if results.error_code != 0:
            raise InvalidArgumentsException("bad token")
        # FIXME: check that at least some results are returned.

        if results.data[0].has_key("profile_id"):
            profile_id = results.data[0]["profile_id"]

        return self.edit({
            'id': machine_id,
            'hostname': hostname,
            'ip_address': ip_addr,
            'mac_address': mac_addr,
            'profile_id': profile_id
         })


    def cobbler_sync(self, data):
         cobbler_api = config_data.Config().cobbler_api
         profiles = profile.Profile().list(None, {}).data
         provisioning.CobblerTranslatedSystem(cobbler_api, profiles, data, is_virtual=True)

    # for duck typing compatibility w/ machine           
    def new(self, token):
         args = {}
         self.logger.info("deployment_new")
         return self.add(token, args)    

    def add(self, token, args):
        """
        Create a deployment.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of deployment arguments.
        @type args: dict
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - mac_address (optional)
            - machine_id
            - profile_id
            - state
            - display_name
            - netboot_enabled (optional)
            - puppet_node_diff (optional)
            - is_locked (optional)
        @raise SQLException: On database error
        """
        mac = None
        profilename = None
        required = ('machine_id', 'profile_id', 'state', 'display_name')
        optional =\
            ('hostname', 'ip_address', 'registration_token', 'mac_address', 'netboot_enabled', 
             'puppet_node_diff', 'is_locked')
        validator = FieldValidator(args)
        validator.verify_required(required)
        validator.verify_printable('puppet_node_diff')
        
        # find highest deployment id
        all_deployments = self.list(token, {})

        try:
            machine_obj = machine.Machine()
            machine_result = machine_obj.get(token, { "id" : args["machine_id"]})
            mac = machine_result.data["mac_address"]
        except VirtFactoryException:
            raise OrphanedObjectException(invalid_fields={'machine_id':REASON_ID})

        try:
            profile_obj = profile.Profile()
            result = profile_obj.get(token, { "id" : args["profile_id"]})
            profilename = result.data["name"]
        except VirtFactoryException:
            raise OrphanedObjectException(invalid_fields={'profile_id':REASON_ID})

        display_name = mac + " / " + profilename
        
        args["display_name"] = display_name
        args["netboot_enabled"] = 0
        args["mac_address"] = self.generate_mac_address(all_deployments.data[-1]["id"])
        args["state"] = DEPLOYMENT_STATE_CREATING
        args["netboot_enabled"] = 0 # never PXE's
        args["registration_token"] = regtoken.RegToken().generate(token)

        # cobbler sync must run with a filled in item in the database, so we must commit
        # prior to running cobbler sync
         
        session = db.open_session()
        try:
            deployment = db.Deployment()
            deployment.update(args)
            session.save(deployment)
            session.flush()
            self.cobbler_sync(deployment.data())
            args["id"] = results.data
            self.__queue_operation(token, args, TASK_OPERATION_INSTALL_VIRT) 
            return success(deployment.id)
        finally:
            session.close()


    def generate_mac_address(self, id):
         # pick an offset into the XenSource range as given by the highest used object id
         # FIXME: verify that sqlite id fields work as counters and don't fill in on deletes
         # FIXME: verify math below
         x = id + 1
         high = x / (127*256)
         mid  = (x % (127*256)) / 256
         low  = x % 256 
         return ":".join([ "00", "16", "3E", "%02x" % high, "%02x" % mid, "%02x" % low ])

    def edit(self, token, args):
        """
        Edit a deployment.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of deployment arguments.
        @type args: dict
            - id
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - mac_address (optional)
            - machine_id  (optional)
            - state  (optional)
            - display_name  (optional)
            - netboot_enabled (optional)
            - puppet_node_diff (optional)
            - is_locked (optional)
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        mac = None
        profilename = None
        required = ('id',)
        optional =\
            ('machine_id', 'state', 'display_name', 'hostname', 'ip_address', 'registration_token',
             'mac_address', 'netboot_enabled', 'puppet_node_diff', 'is_locked')
        filter = ('id', 'profile_id')
        validator = FieldValidator(args)
        validator.verify_required(required)
        validator.verify_printable('puppet_node_diff')
         
        try:
            machine_obj = machine.Machine()
            result = machine_obj.get(token, { "id" : args["machine_id"]})
            mac = result.data["mac_address"]
        except VirtFactoryException:
            raise InvalidArgumentsException(invalid_fields={"machine_id":REASON_ID})

        try:
            profile_obj = profile.Profile()
            result = profile_obj.get(token, { "id" : args["profile_id"] })
            profilename = result.data["name"]
        except VirtFactoryException:
            raise InvalidArgumentsException(invalid_fields={"machine_id":REASON_ID})

        display_name = mac + "/" + profilename
        args["display_name"] = display_name
        args["netboot_enabled"] = 0 # never PXE's

        session = db.open_session()
        try:
            deployment = db.Deployment.get(session, args['id'])
            deployment.update(args, filter)
            session.save(deployment)
            session.flush()
            self.cobbler_sync(deployment.data())
            return success()
        finally:
            session.close()
     

    def __set_locked(self, token, args, dep_state=DEPLOYMENT_STATE_PENDING, lock=True):
        session = db.open_session()
        try:
            deployment = db.Deployment.get(session, args['id'])
            deployment.state = dep_state
            if lock:
                deployment.is_locked = 1
            else:
                deployment.is_locked = 0
            session.save(deployment)
            session.flush()
            self.cobbler_sync(deployment.data())
            return success()
        finally:
            session.close()
            
        self.edit(token, args)
     
    def set_state(self, token, args, status_code):
        session = db.open_session()
        try:
            deployment = db.Deployment.get(session, args['id'])
            deployment.state = status_code
            session.save(deployment)
            session.flush()
            self.cobbler_sync(deployment.data())
            return success()
        finally:
            session.close()

    def delete(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_DELETING, True)
        self.__queue_operation(token, dargs, TASK_OPERATION_DELETE_VIRT)
        return success() # FIXME: always?

    def pause(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_PAUSING, True)
        self.__queue_operation(token, dargs, TASK_OPERATION_PAUSE_VIRT)
        return success()

    def unpause(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_UNPAUSING, True)
        self.__queue_operation(token, dargs, TASK_OPERATION_UNPAUSE_VIRT)
        return success()

    def shutdown(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_STOPPING, True)
        self.__queue_operation(token, dargs, TASK_OPERATION_SHUTDOWN_VIRT)
        return success()
    
    def destroy(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_STOPPING, True)
        self.__queue_operation(token, dargs, TASK_OPERATION_DESTROY_VIRT)
        return success()

    def start(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_STARTING, True)
        self.__queue_operation(token, dargs, TASK_OPERATION_START_VIRT)
        return success()

    def database_delete(self, token, args):
        """
        Deletes a deployment in the database.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of deployment attributes.
            - id
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            db.Deployment.delete(session, args['id'])
            return success()
        finally:
            session.close()


    def list(self, token, args):
        """
        Get a list of all deployments.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of query arguments.
        @type args: dict
            - offset (optional)
            - limit (optional)
        @return: A list of deployments.
        @rtype: [dict,]
            - id
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - mac_address (optional)
            - machine_id  (optional)
            - state  (optional)
            - display_name  (optional)
            - netboot_enabled (optional)
            - puppet_node_diff (optional)
            - is_locked (optional)
        @raise SQLException: On database error
        """
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            for deployment in db.Deployment.list(session, offset, limit):
                result.append(self.expand(deployment))
            return success(result)
        finally:
            session.close()


    def __queue_operation(self, token, args, task_operation):
        
         obj = self.get(token, { "id" : args["id"] })
         if not obj.ok():
             raise NoSuchObjectException()

         task_obj = task.Task()
         task_obj.add(token, {
            "user_id"       : -1,  # FIXME: obtain from token
            "machine_id"    : args["machine_id"],
            "deployment_id" : args["id"],
            "action_type"   : task_operation,
            "state"         : TASK_STATE_QUEUED
         })


    def get_by_hostname(self, token, args):
        """
        Get deployments by hostname.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of query attributes.
            - hostname
            - offset (optional)
            - limit (optional)
        @type args: dict
        @return: A list of deployments.
        @rtype: [dict,]
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - mac_address (optional)
            - machine_id
            - profile_id
            - state
            - display_name
            - netboot_enabled (optional)
            - puppet_node_diff (optional)
            - is_locked (optional)
        @raise SQLException: On database error
        """
        required = ('hostname',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            hostname = args['hostname']
            offset, limit = self.offset_and_limit(args)
            query = session.query(db.Deployment)
            for deployment in query.select_by(hostname == hostname, offset=offset, limit=limit):
                result.append(self.expand(deployment))
            return success(result)
        finally:
            session.close()


    def get_by_regtoken(self, token, args):
        """
        Get deployments by registration token.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of query attributes.
            - registration_token
            - offset (optional)
            - limit (optional)
        @type args: dict
        @return: A list of deployments.
        @rtype: [dict,]
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - mac_address (optional)
            - machine_id
            - profile_id
            - state
            - display_name
            - netboot_enabled (optional)
            - puppet_node_diff (optional)
            - is_locked (optional)
        @raise SQLException: On database error
        """
        required = ('registration_token',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            regtoken = args['registration_token']
            offset, limit = self.offset_and_limit(args)
            query = session.query(db.Deployment)
            for deployment in query.select_by(registration_token == regtoken, offset=offset, limit=limit):
                result.append(self.expand(deployment))
            return success(result)
        finally:
            session.close()


    def refresh(self, token, args):
         """
         Most all node actions are out of band (scheduled) but we need
         the current state when loading the edit page
         """

         dargs = self.get(token, { "id" : args["id"] }).data

         self.logger.info("running refresh code")
         cmd = [
            "/usr/bin/vf_nodecomm",
            socket.gethostname(),
            dargs["machine"]["hostname"],
            "virt_status",
            dargs["mac_address"]
         ]
         p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
         data = p1.communicate()[0]
         lines = data.split("\n")
         self.logger.info("output = %s" % data)
         for line in lines:
             if line.find("STATE=running") != -1:
                dargs["state"] = "running"
                return self.edit(token, dargs)
             elif line.find("STATE=paused") != -1:
                dargs["state"] = "paused"
                return self.edit(token, dargs)
             elif line.find("STATE=off") != -1:
                dargs["state"] = "off"
                return self.edit(token, dargs)
         self.logger.info("no match")
         return success()  # FIXME: should this be failure?        

        
    def get(self, token, args):
        """
        Get a deployment by id.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of query attributes.
            - id
        @type args: dict
        @return: A deployment.
        @rtype: dict
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - mac_address (optional)
            - machine_id
            - profile_id
            - state
            - display_name
            - netboot_enabled (optional)
            - puppet_node_diff (optional)
            - is_locked (optional)
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            deployment = db.Deployment.get(session, args['id'])
            return success(self.expand(deployment))
        finally:
            session.close()


    def expand(self, deployment):
        result = deployment.data()
        result['machine'] = deployment.machine.data()
        result['profile'] = deployment.profile.data()
        return result


methods = Deployment()
register_rpc = methods.register_rpc

