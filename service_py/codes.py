# error codes for the web service.
# eventually __main__ will autogenerate a Ruby version

ERR_SUCCESS = 0
ERR_TOKEN_EXPIRED = 1
ERR_TOKEN_INVALID = 2
ERR_USER_INVALID  = 3
ERR_PASSWORD_INVALID = 4
ERR_INTERNAL_ERROR = 5 
ERR_INVALID_ARGUMENTS = 6
ERR_NO_SUCH_OBJECT = 7

def result(rc, variables=[]):
   if rc != ERR_SUCCESS:
      return (False, rc, variables)
   else:
      return (True, rc, variables)

