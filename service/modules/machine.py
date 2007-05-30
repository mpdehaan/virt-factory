"""
Virt-factory backend code.

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Scott Seago <sseago@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""


from server.codes import *

import baseobj
import profile
import cobbler
import provisioning
import web_svc
import regtoken
import deployment
from server import config_data

import threading
import traceback

class Machine(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"machine_add": self.add,
                        "machine_new": self.new,
                        "machine_associate": self.associate,
                        "machine_delete": self.delete,
                        "machine_edit": self.edit,
                        "machine_list": self.list,
                        "machine_get": self.get}
        web_svc.AuthWebSvc.__init__(self)


    def add(self, token, args):
        """
        Create a machine.
        @param args: A dictionary of machine attributes.
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - architecture (optional)
            - processor_speed (optional)
            - processor_count  (optional)
            - memory (optional)
            - kernel_options  (optional)
            - kickstart_metadata (optional)
            - list_group (optional)
            - mac_address (optional)
            - is_container (optional)
            - profile_id
            - puppet_node_diff (optional)
            - netboot_enabled (optional)
            - is_locked (optional)
        @type args: dict
        """    
        optional =\
            ('hostname', 'ip_address', 'registration_token', 'architecture', 'processor_speed', 
             'processor_count','memory', 'kernel_options', 'kickstart_metadata', 
             'list_group', 'mac_address', 'is_container', 'puppet_node_diff', 'netboot_enabled', 'is_locked')
        required = ('profile_id')
        self.__validate(args, required)
        session = db.open_session()
        try:
            machine = db.Machine()
            for key in (required+optional):
                setattr(machine, key, args.get(key, None))
            # TODO: generate the registration token here and make it actually random and decent.
            machine.registration_token = regtoken.RegToken().generate(token)
            machine.netboot_enabled = 1 # initially, allow PXE, until it registers
            session.save(machine)
            session.flush()
            if machine.profile_id >= 0:
                self.cobbler_sync(data) 
            return success(machine.id)
        finally:
            session.close()

    def cobbler_sync(self, data):
        cobbler_api = config_data.Config().cobbler_api
        profiles = profile.Profile().list(None, {}).data
        provisioning.CobblerTranslatedSystem(cobbler_api, profiles, data, is_virtual=True)
 
    def new(self, token):
        """
        Allocate a new machine record to be fill in later. Return a machine_id
        """
        args = { "profile_id" : -1 }
        return self.add(token, args)


    def associate(self, token, machine_id, hostname, ip_addr, mac_addr, profile_id=None,
                  architecture=None, processor_speed=None, processor_count=None,
                  memory=None):
        """
        Associate a machine with an ip/host/mac address
        """
        self.logger.info("associating...")
        if profile_id:
            self.logger.info("profile_id : %s" % profile_id)
        regtoken_obj = regtoken.RegToken()
        if token is None:
            self.logger.info("token is None???")
        if token != "UNSET":
            results = regtoken_obj.get_by_token(None, { "token" : token })
            self.logger.info("get_by_token")
            self.logger.info("results: %s" % results)
            if results.error_code != 0:
                raise codes.InvalidArgumentsException("bad token")
            # FIXME: check that at least some results are returned.

            if len(results.data) > 0 and results.data[0].has_key("profile_id"):
                profile_id = results.data[0]["profile_id"]

            if profile_id is None:
                profile_id = -1  # the unassigned profile id

        args = {
            'id': machine_id,
            'hostname': hostname,
            'ip_address': ip_addr,
            'mac_address': mac_addr,
            'profile_id': profile_id,
            'architecture' : architecture,
            'processor_speed' : processor_speed,
            'processor_count' : processor_count,
            'netboot_enabled' : 0, # elimiinate PXE install loop
            'memory' : memory
        }
        self.logger.info("%s" % str(args))
        return self.edit(token, args)

        
    def edit(self, token, args):
        """
        Edit a machine.
        @param args: A dictionary of machine attributes.
            - id
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - architecture (optional)
            - processor_speed (optional)
            - processor_count  (optional)
            - memory (optional)
            - kernel_options  (optional)
            - kickstart_metadata (optional)
            - list_group (optional)
            - mac_address (optional)
            - is_container (optional)
            - profile_id
            - puppet_node_diff (optional)
            - netboot_enabled (optional)
            - is_locked (optional)
        @type args: dict
        """
        required = ('id')
        optional =\
            ('hostname', 'ip_address', 'registration_token', 'architecture', 'processor_speed', 
             'processor_count','memory', 'kernel_options', 'kickstart_metadata', 'profile_id', 
             'list_group', 'mac_address', 'is_container', 'puppet_node_diff', 'netboot_enabled', 'is_locked')
        self.__validate(args, required)
        session = db.open_session()
        try:
            objectid = args['id']
            machine = session.get(db.Machine, objectid)
            if machine is None:
                 raise NoSuchObjectException(comment=objectid)
            for key in optional:
                current = getattr(user, key)
                setattr(machine, key, args.get(key, current))
            session.save(machine)
            session.flush()
        finally:
            session.close()
            
        if machine.profile_id >= 0:
            self.cobbler_sync(data)
            
        return success()


    def delete(self, token, args):
        """
        Deletes a machine.
        @param args: A dictionary of machine attributes.
            - id
        @type args: dict
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            objectid = args['id']
            machine = session.get(db.Machine, objectid)
            if machine is None:
                raise NoSuchObjectException(comment=objectid)
            session.delete(machine)
            session.flush()
            return success()
        finally:
            session.close()


    def list(self, token, args):
        """
        Get a list of all machines.
        @param args: A dictionary of machine attributes.
        @type args: dict
        @return A list of all machines.
        @rtype: [dict,]
            - id
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - architecture (optional)
            - processor_speed (optional)
            - processor_count  (optional)
            - memory (optional)
            - kernel_options  (optional)
            - kickstart_metadata (optional)
            - list_group (optional)
            - mac_address (optional)
            - is_container (optional)
            - profile_id
            - puppet_node_diff (optional)
            - netboot_enabled (optional)
            - is_locked (optional)
        """    
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            for machine in session.query(db.Machine).select(offset=offset, limit=limit):
                result.append(machine.data())
            return success(result)
        finally:
            session.close()


    def get_by_hostname(self, token, args):
        """
        Get a machines by hostname.
        @param args: A dictionary of machine attributes.
            - hostname
        @type args: dict
        @return A list of all machines.
        @rtype: [dict,]
            - id
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - architecture (optional)
            - processor_speed (optional)
            - processor_count  (optional)
            - memory (optional)
            - kernel_options  (optional)
            - kickstart_metadata (optional)
            - list_group (optional)
            - mac_address (optional)
            - is_container (optional)
            - profile_id
            - puppet_node_diff (optional)
            - netboot_enabled (optional)
            - is_locked (optional)
        # TODO: nested structures.
        """
        required = ('hostname',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            hostname = args['hostname']
            offset, limit = self.offset_and_limit(args)
            query = session.query(db.Machine)
            for machine in query.select_by(hostname == hostname, offset=offset, limit=limit):
                result.append(machine.data())
            return success(result)
        finally:
            session.close()


    def get_by_regtoken(self, token, args):
        """
        Get a machines by registration token.
        @param args: A dictionary of machine attributes.
            - registration_token
        @type args: dict
        @return A list of machines.
        @rtype: [dict,]
            - id
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - architecture (optional)
            - processor_speed (optional)
            - processor_count  (optional)
            - memory (optional)
            - kernel_options  (optional)
            - kickstart_metadata (optional)
            - list_group (optional)
            - mac_address (optional)
            - is_container (optional)
            - profile_id
            - puppet_node_diff (optional)
            - netboot_enabled (optional)
            - is_locked (optional)
        # TODO: nested structures.
        """
        required = ('registration_token',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            regtoken = args['registration_token']
            offset, limit = self.offset_and_limit(args)
            query = session.query(db.Machine)
            for machine in query.select_by(registration_token == regtoken, offset=offset, limit=limit):
                result.append(machine.data())
            return success(result)
        finally:
            session.close()


    def get(self, token, args):
        """
        Get a machine by id.
        @param args: A dictionary of machine attributes.
            - id
        @type args: dict
        @return A list of machines.
        @rtype: dict
            - id
            - hostname (optional)
            - ip_address (optional)
            - registration_token (optional)
            - architecture (optional)
            - processor_speed (optional)
            - processor_count  (optional)
            - memory (optional)
            - kernel_options  (optional)
            - kickstart_metadata (optional)
            - list_group (optional)
            - mac_address (optional)
            - is_container (optional)
            - profile_id
            - puppet_node_diff (optional)
            - netboot_enabled (optional)
            - is_locked (optional)
        # TODO: nested structures.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            objectid = args['id']
            machine = session.get(db.Machine, objectid)
            if machine is None:
                raise NoSuchObjectException(comment=machineid)
            return success(machine.data())
        finally:
            session.close()

            
    def __validate(self, args, required):
        validator = FieldValidator(args)
        validator.verify_required(required)
        validator.verify_enum('architecture', VALID_ARCHS)
        validator.verify_int('processor_speed', 'processor_count', 'memory')
        validator.verify_printable(
               'kernel_options', 'kickstart_metadata', 'list_group', 
               'list_group', 'puppet_node_diff')


methods = Machine()
register_rpc = methods.register_rpc


