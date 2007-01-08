"""
ShadowManager backend code.

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>
Scott Seago <sseago@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import exceptions
import string
import sys
import traceback

# internal codes for the types of operations (used by validation logic)
OP_ADD = 101
OP_EDIT = 102
OP_DELETE = 103
OP_LIST = 104
OP_METHOD = 105
OP_GET = 106

# error codes for the web service.
SUCCESS = ERR_SUCCESS = 0
ERR_TOKEN_EXPIRED = 1
ERR_TOKEN_INVALID = 2
ERR_USER_INVALID  = 3
ERR_PASSWORD_INVALID = 4
ERR_INTERNAL_ERROR = 5 
ERR_INVALID_ARGUMENTS = 6
ERR_NO_SUCH_OBJECT = 7
ERR_ORPHANED_OBJECT = 8
ERR_SQL = 9
ERR_MISCONFIGURED = 10
ERR_INVALID_METHOD = 11
ERR_UNCAUGHT = 999

# architecture field for machines and images
ARCH_X86 = 200
ARCH_X86_64 = 201
ARCH_IA64 = 202
VALID_ARCHS = [ ARCH_X86, ARCH_X86_64, ARCH_IA64 ]

# used to convert to cobbler values
COBBLER_ARCH_MAPPING = {
   ARCH_X86    : "x86",
   ARCH_X86_64 : "x86_64",
   ARCH_IA64   : "ia64"
}

# image valid_targets field 
IMAGE_IS_VIRT = 301
IMAGE_IS_BAREMETAL = 302
IMAGE_IS_EITHER = 303
VALID_TARGETS = [ IMAGE_IS_VIRT, IMAGE_IS_BAREMETAL, IMAGE_IS_EITHER ]

# machine is_container values
MACHINE_IS_CONTAINER = 1
MACHINE_IS_NOT_CONTAINER = 0
VALID_CONTAINERS = [ MACHINE_IS_CONTAINER, MACHINE_IS_NOT_CONTAINER ]

# failure codes for invalid arguments
REASON_NONE  = 400
REASON_RANGE = 401
REASON_ID = 402
REASON_TYPE = 403
REASON_REQUIRED = 404
xREASON_FORMAT = 405
REASON_NOFILE = 406

class ShadowManagerException(exceptions.Exception):
   error_code = ERR_INTERNAL_ERROR

   def __init__(self, **kwargs):
       self.job_id         = self.load(kwargs,"job_id")
       self.stacktrace     = self.load(kwargs,"stacktrace")
       self.invalid_fields = self.load(kwargs,"invalid_fields")
       self.data           = self.load(kwargs,"data")
       self.comment        = self.load(kwargs,"comment")
       self.tb_data = traceback.extract_stack()
       exceptions.Exception.__init__(self)


   def format(self):
      str = """
Exception Name: %s
Exception Comment: %s
Exception Data: %s
Stack Trace:
%s""" % (self.__class__, self.comment, self.data,
         string.join(traceback.format_list(self.tb_data)))

      return str
      #"
   

   def ok(self):
       return self.error_code == 0
 
   def load(self,hash,key,default=None):
       if hash.has_key(key):
           return hash[key]
       else:
           return default

   def __get_additional_data(self):
       data = {}
       if not self.job_id is None:
           data["job_id"] = self.job_id
       if not self.stacktrace is None:
           data["stacktrace"] = self.stacktrace
       if not self.invalid_fields is None:
           data["invalid_fields"] = self.invalid_fields
       if not self.data is None:
           data["data"] = self.data
       if not self.comment is None:
           data["comment"] = self.comment
       return data

   def to_datastruct(self):
       return (self.error_code, self.__get_additional_data())

class SuccessException(ShadowManagerException):
   """
   Not an error / return success and data to caller.
   """
   error_code = ERR_SUCCESS   

class TokenExpiredException(ShadowManagerException):
   """
   The user token that was passed in has been logged out 
   due to inactivity.  Call user_login again.
   """
   error_code = ERR_TOKEN_EXPIRED

class TokenInvalidException(ShadowManagerException):
   """
   The user token doesn't exist, so this function call isn't 
   permitted.  Call user_login to get a valid token.
   """
   error_code = ERR_TOKEN_INVALID

class UserInvalidException(ShadowManagerException):
   """
   Can't log in this user since the user account doesn't 
   exist in the database.
   """
   error_code = ERR_USER_INVALID

class PasswordInvalidException(ShadowManagerException):
   """
   Wrong password.  Bzzzt.  Try again.
   """
   error_code = ERR_PASSWORD_INVALID

class InternalErrorException(ShadowManagerException):
   """
   FIXME: This is a generic error code, and if something is 
   throwing that error, it probably
   should be changed to throw something more specific.
   """
   error_code = ERR_INTERNAL_ERROR

class InvalidArgumentsException(ShadowManagerException):
   """
   The arguments passed in to this function failed to pass 
   validation.  See additional_data for the
   names of which arguments were rejected.
   """
   error_code = ERR_INVALID_ARGUMENTS

class NoSuchObjectException(ShadowManagerException):
   """
   The id passed in doesn't refer to an object.
   """
   error_code = ERR_NO_SUCH_OBJECT

class InvalidMethodException(ShadowManagerException):
   """The method called does not exist"""
   error_code = ERR_INVALID_METHOD

class UncaughtException(ShadowManagerException):
   """
   The python code choked.  additional_data contains the 
   stacktrace, and it's ok to give the stacktrace
   since the user is already logged in.  user_login shouldn't 
   give stacktraces for security reasons.
   """
   error_code = ERR_UNCAUGHT

class OrphanedObjectException(ShadowManagerException):
   """
   A delete can't proceed because another object references 
   this one, or an add can't proceed because a
   referenced object doesn't exist.
   """
   error_code = ERR_ORPHANED_OBJECT

class SQLException(ShadowManagerException):
   """
   The code died inside a SQL call.  This is probably 
   a sign that the validation prior to making
   the call needs to be improved, or maybe SQL was just 
   more efficient (i.e. referential integrity).
   """
   error_code = ERR_SQL

class MisconfiguredException(ShadowManagerException):
   """
   The shadowmanager service isn't properly configured and 
   no calls can be processed until this is corrected on the 
   server side.  The UI/WUI/etc is non-functional and should 
   display a splash screen telling the user to finish their 
   setup of the shadowmanager service by running "shadow init", edit
   /var/lib/shadowmanager/settings, and then run "shadow import".
   """
   error_code = ERR_MISCONFIGURED

def success(data=None,job_id=None):
   """
   Shortcut around success exception that returns equivalent data 
   w/o raise.
   """
   ret = SuccessException(data=data, job_id=job_id)
   return ret


if __name__ == "__main__":
   # run this module as main to generate a ruby compatible constants
   # file.
   module = sys.modules[__name__]
   for x in sorted(module.__dict__.keys()):
       obj = module.__dict__[x]
       if type(obj) == int:
           print "%s = %s" % (x, obj)
