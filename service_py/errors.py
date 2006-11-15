
import exceptions
from codes import *

class ShadowManagerException(exceptions.Exception):
   error_code = ERR_INTERNAL_ERROR

   def __init__(self, additional_data=0):
       self.additional_data = additional_data

class SuccessException(ShadowManagerException):
   error_code = ERR_SUCCESS   

class TokenExpiredException(ShadowManagerException):
   error_code = ERR_TOKEN_EXPIRED

class TokenInvalidException(ShadowManagerException):
   error_code = ERR_TOKEN_INVALID

class UserInvalidException(ShadowManagerException):
   error_code = ERR_USER_INVALID

class PasswordInvalidException(ShadowManagerException):
   error_code = ERR_PASSWORD_INVALID

class InternalErrorException(ShadowManagerException):
   error_code = ERR_INTERNAL_ERROR

class InvalidArgumentsException(ShadowManagerException):
   error_code = ERR_INVALID_ARGUMENTS

class NoSuchObjectException(ShadowManagerException):
   error_code = ERR_NO_SUCH_OBJECT



