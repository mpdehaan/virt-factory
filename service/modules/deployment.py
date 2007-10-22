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
from server import db
from fieldvalidator import FieldValidator

import time
import profile
import machine
import web_svc
import task
import regtoken
import provisioning
import tag
from server import config_data

import re
import subprocess
import socket
import traceback


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
                        "deployment_set_state": self.set_state,
                        "deployment_delete": self.delete,
                        "deployment_list": self.list,
                        "deployment_get": self.get,
			"deployment_get_by_mac_address": self.get_by_mac_address,
			"deployment_get_by_hostname": self.get_by_hostname,
                        "deployment_get_by_tag": self.get_by_tag,
                        "deployment_add_tag": self.add_tag,
                        "deployment_remove_tag": self.remove_tag}

        web_svc.AuthWebSvc.__init__(self)


    def associate(self, token, deployment_id, machine_id, hostname, ip_addr, mac_addr, profile_id=None,
              architecture=None, processor_speed=None, processor_count=None,
              memory=None):
        """
        Associate a machine with an ip/host/mac address
        """
        self.logger.info("associating...")

        # THIS IS ALL OBSOLETE...
        # determine the profile from the token.
        # FIXME: inefficient. ideally we'd have a retoken.get_by_value() or equivalent
        #regtoken_obj = regtoken.RegToken()
        #if token is None:
        #    self.logger.info("token is None???")
        #results = regtoken_obj.get_by_token(None, { "token" : token })
        #self.logger.info("get_by_token")
        #self.logger.info("results: %s" % results)
        #if results.error_code != 0:
        #    raise InvalidArgumentsException("bad token")
        # FIXME: check that at least some results are returned.

        session = db.open_session()

        deployment = db.Deployment().get(session, deployment_id)
        deployment.machine_id  = machine_id
        deployment.hostname    = hostname
        deployment.ip_address  = ip_addr
        deployment.mac_address = mac_addr
        deployment.profile_id  = profile_id

        session.save(deployment)
        session.flush()
        return success()


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
        @raise SQLException: On database error
        """
        mac = None
        profilename = None
        required = ('machine_id', 'profile_id')
        optional = ('hostname',
                    'ip_address',
                    'registration_token',
                    'mac_address',
                    'netboot_enabled',
                    'puppet_node_diff',
                    'is_locked',
                    'auto_start',
                    'last_heartbeat',
                    'tag_ids')
        self.logger.info(args)
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

        if not args.has_key("auto_start"):
            args["auto_start"] = 1 
       
        # cobbler sync must run with a filled in item in the database, so we must commit
        # prior to running cobbler sync
         
        session = db.open_session()
        try:
            deployment = db.Deployment()
            deployment.update(args)
            session.save(deployment)
            if args.has_key('tag_ids'):
                setattr(deployment, "tags", tag.Tag().tags_from_ids(session,
                                                                 args['tag_ids']))
            session.flush()
            self.cobbler_sync(deployment.get_hash())
            args["id"] = deployment.id
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
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        mac = None
        profilename = None
        required = ('id',)
        optional = ('machine_id', 'state', 'display_name',
                    'hostname', 'ip_address', 'registration_token',
                    'mac_address', 'netboot_enabled', 'puppet_node_diff',
                    'is_locked', 'last_heartbeat','auto_start', 'tag_ids')
        filter = ('id', 'profile_id')
        validator = FieldValidator(args)
        validator.verify_required(required)
        validator.verify_printable('puppet_node_diff', 'tags')

        if args.has_key("machine_id"):
            try:
                machine_obj = machine.Machine()
                result = machine_obj.get(token, { "id" : args["machine_id"]})
                mac = result.data["mac_address"]
            except VirtFactoryException:
                raise InvalidArgumentsException(invalid_fields={"machine_id":REASON_ID})

        if args.has_key("profile_id"):
            try:
                profile_obj = profile.Profile()
                result = profile_obj.get(token, { "id" : args["profile_id"] })
                profilename = result.data["name"]
            except VirtFactoryException:
                raise InvalidArgumentsException(invalid_fields={"machine_id":REASON_ID})

        args["netboot_enabled"] = 0 # never PXE's

        session = db.open_session()
        try:
            deployment = db.Deployment.get(session, args['id'])
            if args.has_key("machine_id") or args.has_key("profile_id"):
                if not args.has_key("machine_id"):
                    mac = deployment["machine"]["mac_address"]
                if not args.has_key("profile_id"):
                    profilename=deployment["profile"]["name"]
                display_name = mac + "/" + profilename
                args["display_name"] = display_name
                
                
            deployment.update(args, filter)
            session.save(deployment)
            if args.has_key('tag_ids'):
                setattr(deployment, "tags", tag.Tag().tags_from_ids(session,
                                                                 args['tag_ids']))
            session.flush()
            self.cobbler_sync(deployment.get_hash())
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
            self.cobbler_sync(deployment.get_hash())
            return success()
        finally:
            session.close()
            
        self.edit(token, args)
    
    def delete(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_PENDING, True)
        self.__queue_operation(token, dargs, TASK_OPERATION_DELETE_VIRT)

        # FIXME/NOTE: there may be situations where the above operation fails in
        # which case it is the job of taskatron to ensure the virtual machine
        # perishes.  It will be removed from the WUI immediately here. This
        # behavior can probably be improved somewhat but seems better than
        # having a non-existant undeletable entry stick around in the WUI.

        session = db.open_session()
        db.Deployment.delete(session, args['id'])

        return success() # FIXME: always?

    def pause(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_PENDING, True)
        self.__queue_operation(token, dargs, TASK_OPERATION_PAUSE_VIRT)
        return success()

    def unpause(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_PENDING, True)
        self.__queue_operation(token, dargs, TASK_OPERATION_UNPAUSE_VIRT)
        return success()

    def shutdown(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_PENDING, True)
        self.__queue_operation(token, dargs, TASK_OPERATION_SHUTDOWN_VIRT)
        return success()
    
    def destroy(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_PENDING, True)
        self.__queue_operation(token, dargs, TASK_OPERATION_DESTROY_VIRT)
        return success()

    def start(self, token, args):
        dargs = self.get(token, { "id" : args["id" ]}).data
        self.__set_locked(token, dargs, DEPLOYMENT_STATE_PENDING, True)
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
        @raise SQLException: On database error
        """

        # it is going to be expensive to query all of the list results
        # for an update.  so right now, we're doing it only for 1-item
        # gets, with the thought that nodes should be sending async
        # updates, or that we are periodically polling them for status

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


    def set_state(self, token, args):
        """
        FIXME: authentication details TBA.
        requires: mac_address, state
        """

        required = ('mac_address','state')
        FieldValidator(args).verify_required(required)
        
        which = self.get_by_mac_address(token,args)
        self.logger.debug("set_state on %s to %s" % (args["mac_address"],args["state"]))
        if which.error_code != 0:
           raise InvalidArgumentsException(comment="missing item")
        if len(which.data) == 0:
           raise InvalidArgumentsException(comment="missing item (no %s)" % args["mac_address"]) 
        id = which.data[0]["id"] 

        session = db.open_session()
        # BOOKMARK 
        deployment = db.Deployment.get(session, id)
        results = self.expand(deployment)

        results["state"] = args["state"]

        # misnomer: this is the time of the last status update
        results["last_heartbeat"] = int(time.time())
  
        self.logger.debug("setting deployment status: %s" % results)
        self.edit(token, results)

        return success(results)



    def add_tag(self, token, args):
        """
        Given  deployment id and tag string, apply the tag to the deployment
        @param token: A security token.
        @type token: string
        @param args: A dictionary of deployment attributes.
            - id
            - tag_id
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id', 'tag_id',)
        FieldValidator(args).verify_required(required)
        deployment = self.get(token, {"id": args["id"]}).data
        tag_id = args["tag_id"]
        tag_ids = deployment["tag_ids"]
        if not int(tag_id) in tag_ids:
            tag_ids.append(int(tag_id))
            self.edit(token, {"id": args["id"], "tag_ids": tag_ids})
        return success()

    def remove_tag(self, token, args):
        """
        Given  deployment id and tag string, remove the tag from the deployment
        @param token: A security token.
        @type token: string
        @param args: A dictionary of deployment attributes.
            - id
            - tag_id
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id', 'tag_id',)
        FieldValidator(args).verify_required(required)
        deployment = self.get(token, {"id": args["id"]}).data
        tag_id = args["tag_id"]
        tag_ids = deployment["tag_ids"]
        if int(tag_id) in tag_ids:
            tag_ids.remove(int(tag_id))
            self.edit(token, {"id": args["id"], "tag_ids": tag_ids})
        return success()

    def get_by_mac_address(self, token, args):
        """
        """
        required = ('mac_address',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            # creation gives uppercase MAC addresses, so be sure
            # we search on the same criteria until the DB search
            # can be made case insensitive.  (FIXME)
            mac_address = args['mac_address'].replace("_",":").upper()
            offset, limit = self.offset_and_limit(args)
            query = session.query(db.Deployment).limit(limit).offset(offset)
            for machine in query.select_by(mac_address = mac_address):
                result.append(self.expand(machine))
            return success(result)
        finally:
            session.close()


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
        @raise SQLException: On database error
        """
        required = ('hostname',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            hostname = args['hostname']
            offset, limit = self.offset_and_limit(args)
            query = session.query(db.Deployment).offset(offset).limit(limit)
            for deployment in query.select_by(hostname=hostname):
                result.append(self.expand(deployment))
            return success(result)
        finally:
            session.close()


    def get_by_regtoken(self, token, args):
        # FIXME: registration tokens are currently non-operational
        # for virt-factory 0.0.3 and later.  This code can be pruned
        # if regtoken usage is not reinstated.
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
        @raise SQLException: On database error
        """
        required = ('registration_token',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            regtoken = args['registration_token']
            offset, limit = self.offset_and_limit(args)
            query = session.query(db.Deployment).offset(offset).limit(limit)
            for deployment in query.select_by(registration_token=regtoken):
                result.append(self.expand(deployment))
            return success(result)
        finally:
            session.close()

    # NOTE: this function removed because we want async state updates
    def refresh(self, token, get_results):
         """
         Most all node actions are out of band (scheduled) but we need
         the current state when loading the edit page
         """

         #dargs = get_results
 
         #self.logger.info("refresh request for: %s" % get_results)
         #this_host = socket.gethostname()
         #cmd = [
         #   "/usr/bin/vf_nodecomm",
         #   this_host,
         #   dargs["machine"]["hostname"],
         #   this_host,
         #   "virt_status",
         #   dargs["mac_address"]
         #]
         #p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
         #data = p1.communicate()[0]
         #lines = data.split("\n")
         #self.logger.info("output = %s" % data)
         #for line in lines:
         #    if line.find("STATE=running") != -1:
         #       dargs["state"] = "running"
         #       return self.edit(token, dargs)
         #    elif line.find("STATE=paused") != -1:
         #       dargs["state"] = "paused"
         #       return self.edit(token, dargs)
         #    elif line.find("STATE=off") != -1:
         #       dargs["state"] = "off"
         #       return self.edit(token, dargs)
         #self.logger.info("no match")
         #return success()  # FIXME: should this be failure?        

        
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
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """


        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            deployment = db.Deployment.get(session, args['id'])
            results = self.expand(deployment)

            self.logger.info("your deployment is: %s" % results)
 
            # we want the state "now" so we must contact the node
            # to update it!
            self.refresh(token, results)

            # now re-get the updated record which will have an
            # accurate state.
            deployment = db.Deployment.get(session, args['id'])
            return success(self.expand(deployment))

        finally:
            session.close()


    def get_by_tag(self, token, args):
        """
        Return a list of all deployments tagged with the given tag
        """
        required = ('tag_id',)
        FieldValidator(args).verify_required(required)
        tag_id = args['tag_id']
        session = db.open_session()
        try:
            name = args['name']
            deployment_tags = db.Database.table['deployment_tags']
            deployments = session.query(db.Deployment).select((deployment_tags.c.tag_id==tag_id &
                                                         deployment_tags.c.deployment_id==db.Deployment.c.id))
            if deployments:
                deployments = self.expand(deployments)
            return codes.success(deployments)
        finally:
            session.close()

    def expand(self, deployment):
        result = deployment.get_hash()
        result['machine'] = deployment.machine.get_hash()
        result['profile'] = deployment.profile.get_hash()
        result['tags'] = []
        result['tag_ids'] = []
        for tag in deployment.tags:
            result['tags'].append(tag.get_hash())
            result['tag_ids'].append(tag.id)
        return result


methods = Deployment()
register_rpc = methods.register_rpc

