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
from codes import *

class ShadowManagerException(exceptions.Exception):
   error_code = ERR_INTERNAL_ERROR

   def __init__(self, additional_data=0):
       self.additional_data = additional_data

class SuccessException(ShadowManagerException):
   """
   Life is good.  This is not an error and returns additional_data to the caller (basically) immediately.
   """
   error_code = ERR_SUCCESS   

class TokenExpiredException(ShadowManagerException):
   """
   The user token that was passed in has been logged out due to inactivity.  Call user_login again.
   """
   error_code = ERR_TOKEN_EXPIRED

class TokenInvalidException(ShadowManagerException):
   """
   The user token doesn't exist, so this function call isn't permitted.  Call user_login to get a valid token.
   """
   error_code = ERR_TOKEN_INVALID

class UserInvalidException(ShadowManagerException):
   """
   Can't log in this user since the user account doesn't exist in the database.
   """
   error_code = ERR_USER_INVALID

class PasswordInvalidException(ShadowManagerException):
   """
   Wrong password.  Bzzzt.  Try again.
   """
   error_code = ERR_PASSWORD_INVALID

class InternalErrorException(ShadowManagerException):
   """
   FIXME: This is a generic error code, and if something is throwing that error, it probably
   should be changed to throw something more specific.
   """
   error_code = ERR_INTERNAL_ERROR

class InvalidArgumentsException(ShadowManagerException):
   """
   The arguments passed in to this function failed to pass validation.  See additional_data for the
   names of which arguments were rejected.
   """
   error_code = ERR_INVALID_ARGUMENTS

class NoSuchObjectException(ShadowManagerException):
   """
   The id passed in doesn't refer to an object.
   """
   error_code = ERR_NO_SUCH_OBJECT

class UncaughtException(ShadowManagerException):
   """
   The python code choked.  additional_data contains the stacktrace, and it's ok to give the stacktrace
   since the user is already logged in.  user_login shouldn't give stacktraces for security reasons.
   """
   error_code = ERR_UNCAUGHT

class OrphanedObjectException(ShadowManagerException):
   """
   A delete can't proceed because another object references this one, or an add can't proceed because a
   referenced object doesn't exist.
   """
   error_code = ERR_ORPHANED_OBJECT

class SQLException(ShadowManagerException):
   """
   The code died inside a SQL call.  This is probably a sign that the validation prior to making
   the call needs to be improved, or maybe SQL was just more efficient (i.e. referential integrity).
   """
   error_code = ERR_SQL

class MisconfiguredException(ShadowManagerException):
   """
   The shadowmanager service isn't properly configured and no calls can be processed until this is
   corrected on the server side.  The UI/WUI/etc is non-functional and should display a splash screen
   telling the user to finish their setup of the shadowmanager service by running "shadow init", edit
   /var/lib/shadowmanager/settings, and then run "shadow import".
   """
   error_code = ERR_MISCONFIGURED
