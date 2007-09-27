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
from server import db
from server import config_data
from fieldvalidator import FieldValidator
import distribution
import cobbler
import provisioning
import profileimporter
import web_svc

from subprocess import *
import os
import tempfile
import threading
import traceback
from xmlrpclib import Binary


class Profile(web_svc.AuthWebSvc):
    def __init__(self):
        self.methods = {"profile_add": self.add,
                        "profile_edit": self.edit,
                        "profile_delete": self.delete,
                        "profile_get": self.get,
			"profile_get_by_name": self.get_by_name,
                        "profile_list": self.list,
                        "profile_import_installed": self.import_installed_profiles,
                        "profile_import_from_upload": self.import_from_upload,
                        "profile_import_from_url": self.import_from_url}
        web_svc.AuthWebSvc.__init__(self)


    def add(self, token, args):
        """
        Create a profile.
        @param token: A security token.
        @type token: string
        @param args: Profile attributes.
        @type args: dict 
        @raise SQLException: On database error
        """
        optional =\
            ('distribution_id', 'virt_storage_size', 'virt_ram', 'virt_type', 
             'kickstart_metadata',
             'kernel_options', 'puppet_classes')
        required = ('name', 'version', 'valid_targets', 'is_container')
        self.validate(args, required)
        session = db.open_session()
        try:
            profile = db.Profile()
            profile.update(args)
            session.save(profile)
            session.flush()
            self.cobbler_sync(profile.get_hash())
        finally:
            session.close()

         
    def cobbler_sync(self, data):
         # make the corresponding cobbler calls.
         cobbler_api = config_data.Config().cobbler_api
         distributions = distribution.Distribution().list(None, {}).data
         provisioning.CobblerTranslatedProfile(cobbler_api ,distributions, data)


    def edit(self, token, args):
        """
        Edit a profile.
        @param token: A security token.
        @type token: string
        @param args: profile attributes.
        @type args: dict 
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        optional =\
            ('name', 'version', 'valid_targets', 'is_container', 'distribution_id', 'virt_storage_size', 
             'virt_ram', 'virt_type', 'kickstart_metadata', 'kernel_options', 'puppet_classes')
        self.validate(args, required)
        session = db.open_session()
        try:
            profile = db.Profile.get(session, args['id'])
            profile.update(args)
            session.save(profile)
            session.flush()
            return success()
        finally:
            session.close()


    def delete(self, token, args):
        """
        Delete a profile.
        @param token: A security token.
        @type token: string
        @param args: The profile id to be deleted.
        @type args: dict 
            - id
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            db.Profile.delete(session, args['id'])
            return success()
        finally:
            session.close()


    def list(self, token, args):
        """
        Get a list of all profiles..
        @param token: A security token.
        @type token: string
        @param args: A dictionary of query properties.
        @type args: dict
            - offset (optional)
            - limit (optional)
        @return: A list of profiles.
        @rtype: [dict,]
        @raise SQLException: On database error
        """
        session = db.open_session()
        try:
            result = []
            offset, limit = self.offset_and_limit(args)
            for profile in db.Profile.list(session, offset, limit):
                result.append(self.expand(profile))
            return success(result)
        finally:
            session.close()


    def get(self, token, args):
        """
        Get a profile by id.
        @param token: A security token.
        @type token: string
        @param args: The profile id.
        @type args: dict 
            - id
        @return: A profile.
        @rtype: dict
        @raise SQLException: On database error
        @raise NoSuchObjectException: On object not found.  
        """
        required = ('id',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            self.logger.info(args)
            profile = db.Profile.get(session, args['id'])
            return success(self.expand(profile))
        finally:
            session.close()


    def get_by_name(self, token, args):
        """
        Get a profile by name.
        @param token: A security token.
        @type token: string
        @param args: The profile name.
        @type args: dict 
            - name
        @return: A profile.
        @rtype: dict
        @raise SQLException: On database error
        """
        required = ('name',)
        FieldValidator(args).verify_required(required)
        session = db.open_session()
        try:
            name = args['name']
            profile = session.query(db.Profile).selectfirst_by(name = name)
            if profile:
                profile = self.expand(profile)
            return success(profile)
        finally:
            session.close()


    def validate(self, args, required):
        vdr = FieldValidator(args)
        vdr.verify_required(required)
        vdr.verify_printable('name', 'version', 'kernel_options', 'puppet_classes', 'virt_type')
        vdr.verify_int(['virt_storage_size', 'virt_ram'])
        vdr.verify_enum('valid_targets', VALID_TARGETS)
        vdr.verify_enum('is_container', VALID_CONTAINERS)


    def expand(self, profile):
        result = profile.get_hash()
        result['distribution'] = profile.distribution.get_hash()
        return result

    def import_from_upload(self, token, args):
        orig_filename = args["filename"]
        data = args["file"]
        data.decode
        
        fd, filename = tempfile.mkstemp(orig_filename)
        try:
            file=os.fdopen(fd, 'w+b')
            file.write(data.data)
            file.close()
            retval = self.import_profile_internal(token, orig_filename, filename, args["force"])
        finally:
            os.remove(filename)
        return retval
        
    def import_from_url(self, token, args):
        """
        Import a profile
        @param token: A security token.
        @type token: string
        @param package_url: URL to the RPM for the profile to be installed
        @type package_url: string
        @param force: Whether to force install even if the same version of this profile is already installed
        @type force: boolean
        @return: 
        @rtype: 
        """
        return self.import_profile_internal(token, args["url"], args["url"], args["force"])

    def import_profile_internal(self, token, visible_name, profile_package, force):
        """
        Import a profile
        @param token: A security token.
        @type token: string
        @param visible_name: original filename/url to diplay in error messages
        @type visible_name: string
        @param profile_package: URL or pathname to the RPM for the profile to be installed
        @type profile_package: string
        @param force: Whether to force install even if the same version of this profile is already installed
        @type force: boolean
        @return: 
        @rtype: 
        """
        # RPM must provide vf-profile
        check_provides_cmd = ['/bin/rpm', '-q', '--provides', '-p', profile_package]
        cmd_out, error_msg, exit_code = self.run_external_command(check_provides_cmd)
        if (exit_code != 0):
            self.logger.error("error in validating RPM " + ' '.join(check_provides_cmd))
            self.logger.error(error_msg)
            raise InvalidArgumentsException(comment=error_msg)
        else:
            self.logger.info("provides query returned " + ' '.join(cmd_out))
        found_vf_profile=False
        for line in cmd_out:
            if line.strip() == 'vf-profile':
                found_vf_profile=True
                break
        if not found_vf_profile:
            raise InvalidArgumentsException(comment=visible_name + " does not provide vf-profile")
        rpm_install_cmd = ['/bin/rpm', '-Uvh', profile_package]
        if force:
            rpm_install_cmd.insert(2, "--force")
        cmd_out, error_msg, exit_code = self.run_external_command(rpm_install_cmd)
        if (exit_code != 0):
            self.logger.error("error in installing RPM " + ' '.join(rpm_install_cmd))
            self.logger.error(error_msg)
            raise ProfileImportException(comment=error_msg)
        else:
            self.logger.info("RPM install returned " + ' '.join(cmd_out))
        self.import_installed_profiles(token)
        return success()

    def run_external_command(self, cmdline):
        pipe = Popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        cmd_out = pipe.stdout.readlines()
        error_msg = pipe.stderr.read().strip()
        exit_code = pipe.wait()
        return cmd_out, error_msg, exit_code
        
    def import_installed_profiles(self, token, profile_name=None, force_all=False):
        """
        Import currently installed profiles
        @param token: A security token.
        @type token: string
        @param profile_name: The profile to import, if specifying a single profile
        @type profile_name: string
        @param force_all: Whether to force re-import of all profiles
        @type force_all: boolean
        @return: 
        @rtype: 
        @raise SQLException: On database error
        """
        profileimporter.ProfileImporter(self.logger, profile_name, force_all).run_import()
        return success()

methods = Profile()
register_rpc = methods.register_rpc


