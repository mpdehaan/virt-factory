"""
Virt-factory backend code.

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Scott Seago <sseago@redhat.com>
Adrian Likins <alikins@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""


from server import codes
from server import db
from fieldvalidator import FieldValidator

import profile
import provisioning
import deployment
import web_svc
import regtoken
import tag
from server import config_data

import re

class Machine(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"machine_add": self.add,
                        "machine_new": self.new,
                        "machine_associate": self.associate,
                        "machine_delete": self.delete,
                        "machine_edit": self.edit,
                        "machine_list": self.list,
                        "machine_get": self.get,
			"machine_get_by_hostname": self.get_by_hostname,
			"machine_get_by_mac_address": self.get_by_mac_address,
                        "machine_get_profile_choices": self.get_profile_choices,
                        "machine_get_by_tag": self.get_by_tag,
                        "machine_add_tag": self.add_tag,
                        "machine_remove_tag": self.remove_tag
        }
        web_svc.AuthWebSvc.__init__(self)


    def add(self, token, args):
        """
        Create a machine.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of machine attributes.
        @type args: dict
        @raise SQLException: On database error
        """    
        optional = (
            'hostname', 'ip_address', 'registration_token', 
            'architecture', 'processor_speed', 
            'processor_count','memory', 'kernel_options', 
            'kickstart_metadata', 'list_group', 'mac_address', 
            'is_container', 'puppet_node_diff', 
            'netboot_enabled', 'is_locked', 'status',
            'last_heartbeat', 'tag_ids'
        )
        required = ('profile_id',)
        self.validate(args, required)
        session = db.open_session()
        try:
            machine = db.Machine()
            machine.update(args)
            machine.registration_token = regtoken.RegToken().generate(token)
            machine.netboot_enabled = 1 # initially, allow PXE, until it registers
            session.save(machine)
            if args.has_key('tag_ids'):
                setattr(machine, "tags", tag.Tag().tags_from_ids(session,
                                                                 args['tag_ids']))
            session.flush()
            if machine.profile_id >= 0:
                self.cobbler_sync(machine.get_hash()) 
            return codes.success(machine.id)
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


    def associate(self, token, machine_id, machine_id_junk, hostname, ip_addr, mac_addr, profile_id=None,
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
        @param token: A security token.
        @type token: string
        @param args: A dictionary of machine attributes.
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        optional = (
             'hostname', 'ip_address', 'registration_token', 
             'architecture', 'processor_speed', 
             'processor_count','memory', 'kernel_options', 
             'kickstart_metadata', 'profile_id', 
             'list_group', 'mac_address', 'is_container', 
             'puppet_node_diff', 'netboot_enabled', 'is_locked',
             'state', 'last_heartbeat', 'tag_ids'
        )
        self.validate(args, required)
        session = db.open_session()
        try:
            machine = db.Machine.get(session, args['id'])
            machine.update(args)
            session.save(machine)
            if args.has_key('tag_ids'):
                setattr(machine, "tags", tag.Tag().tags_from_ids(session,
                                                                 args['tag_ids']))
            session.flush()
            if machine.profile_id >= 0:
                self.cobbler_sync(machine.get_hash())
            return codes.success()
        finally:
            session.close()


    def delete(self, token, args):
        """
        Deletes a machine.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of machine attributes.
            - id
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            db.Machine.delete(session, args['id'])
            return codes.success()
        finally:
            session.close()


    def list(self, token, args):
        """
        Get a list of all machines.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of machine attributes.
        @type args: dict
            - offset (optional)
            - limit (optional)
        @return A list of all machines.
        @rtype: [dict,]
        @raise SQLException: On database error
        """    
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            for machine in db.Machine.list(session, offset, limit):
                result.append(self.expand(machine))
            return codes.success(result)
        finally:
            session.close()


    def get_by_hostname(self, token, args):
        """
        Get a machines by hostname.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of machine attributes.
            - hostname
            - offset (optional)
            - limit (optional)
        @type args: dict
        @return A list of all machines.
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
            query = session.query(db.Machine).offset(offset).limit(limit)
            for machine in query.select_by(hostname = hostname):
                result.append(self.expand(machine))
            return codes.success(result)
        finally:
            session.close()

    def get_profile_choices(self, token, args={}):
        """
        Returns the list of profiles that can be installed on this given host
        """

        this_object = self.get(token,{ "id" : args["id" ] })
        this_object = this_object.data
        try:
            # the WUI should filter this out but lets be safe anyway
            if this_object["profile"]["is_container"] != codes.MACHINE_IS_CONTAINER:
                # cannot install any virt types on this machine
                return codes.success([])

            need_virt = this_object["profile"]["virt_type"]
            need_arch = this_object["profile"]["distribution"]["architecture"]
        except KeyError, e:
            #missing distribution or profile, for now return empty list rather than error
            print "missing distribution or profile, for now return empty list rather than error", e
            print "machine: ", this_object
            return codes.success([])

        # find all profiles with matching virt types and matching arches
        # matching distros is not important.
        try:
            session = db.open_session()
            offset, limit = self.offset_and_limit(args)        
            
            query = session.query(db.Profile).offset(offset).limit(limit)
            results = []
            # FIXME: make efficient .. want to send raw SQL to sqlalchemy
            # to do fancy joins
            for result in query.select():
                print "trying", result
                if result.distribution.architecture == need_arch and result.virt_type == need_virt:
                    obj = profile.Profile().get(token, { "id" : result.id })
                    print "found", obj
                    results.append(obj.data)
            return codes.success(results)
        finally:
            session.close()

    def add_tag(self, token, args):
        """
        Given  machine id and tag string, apply the tag to the machine
        @param token: A security token.
        @type token: string
        @param args: A dictionary of machine attributes.
            - id
            - tag_id
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id', 'tag_id',)
        FieldValidator(args).verify_required(required)
        machine = self.get(token, {"id": args["id"]}).data
        tag_id = args["tag_id"]
        tag_ids = machine["tag_ids"]
        if not int(tag_id) in tag_ids:
            tag_ids.append(int(tag_id))
            self.edit(token, {"id": args["id"], "tag_ids": tag_ids})
        return codes.success()

    def remove_tag(self, token, args):
        """
        Given  machine id and tag string, remove the tag from the machine
        @param token: A security token.
        @type token: string
        @param args: A dictionary of machine attributes.
            - id
            - tag_id
        @type args: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id', 'tag_id',)
        FieldValidator(args).verify_required(required)
        machine = self.get(token, {"id": args["id"]}).data
        tag_id = args["tag_id"]
        tag_ids = machine["tag_ids"]
        if int(tag_id) in tag_ids:
            tag_ids.remove(int(tag_id))
            self.edit(token, {"id": args["id"], "tag_ids": tag_ids})
        return codes.success()

    def get_by_regtoken(self, token, args):
        # FIXME: this code is currently non-operational in VF 0.0.3 and later
        # this code can be pruned if regtoken functional is needed and
        # reinstated.
        """
        Get a machines by registration token.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of machine attributes.
            - registration_token
            - offset (optional)
            - limit (optional)
        @type args: dict
        @return A list of machines.
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
            query = session.query(db.Machine).offset(offset).limit(limit)
            for machine in query.select_by(registration_token = regtoken):
                result.append(self.expand(machine))
            return codes.success(result)
        finally:
            session.close()


    def get_by_mac_address(self, token, args):
        """
        """
        required = ('mac_address',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            result = []
            mac_address = args['mac_address']
            offset, limit = self.offset_and_limit(args)
            query = session.query(db.Machine).limit(limit).offset(offset)
            for machine in query.select_by(mac_address = mac_address):
                result.append(self.expand(machine))
            return codes.success(result)
        finally:
            session.close()


    def get(self, token, args):
        """
        Get a machine by id.
        @param token: A security token.
        @type token: string
        @param args: A dictionary of machine attributes.
            - id
        @type args: dict
        @return A machine.
        @rtype: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            self.logger.info(args)
            machine = db.Machine.get(session, args['id'])
            return codes.success(self.expand(machine))
        finally:
            session.close()


    def get_by_tag(self, token, args):
        """
        Return a list of all machines tagged with the given tag
        """
        required = ('tag_id',)
        FieldValidator(args).verify_required(required)
        tag_id = args['tag_id']
        session = db.open_session()
        try:
            name = args['name']
            machine_tags = db.Database.table['machine_tags']
            machines = session.query(db.Machine).select((machine_tags.c.tag_id==tag_id &
                                                         machine_tags.c.machine_id==db.Machine.c.id))
            if machines:
                machines = self.expand(machines)
            return codes.success(machines)
        finally:
            session.close()

    def validate(self, args, required):
        vdr = FieldValidator(args)
        vdr.verify_required(required)
        # this code doesn't work, so commenting out for now -- MPD
        # vdr.verify_enum('architecture', codes.VALID_ARCHS)
        # vdr.verify_int(['processor_speed', 'processor_count', 'memory'])
        vdr.verify_printable(
               'kernel_options', 'kickstart_metadata', 'list_group', 
               'list_group', 'puppet_node_diff', 'tags')


    def expand(self, machine):
        result = machine.get_hash()
        result['profile'] = machine.profile.get_hash()
        result['profile']['distribution'] = machine.profile.distribution.get_hash()
        result['tags'] = []
        result['tag_ids'] = []
        for tag in machine.tags:
            result['tags'].append(tag.get_hash())
            result['tag_ids'].append(tag.id)
        return result


methods = Machine()
register_rpc = methods.register_rpc

