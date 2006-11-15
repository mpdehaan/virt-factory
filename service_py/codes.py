
# used for specifying types of validation required, and so forth.
# internal to python code and of no concern to clients of the service.

OP_ADD = 1
OP_EDIT = 2
OP_DELETE = 3
OP_LIST = 4
OP_METHOD = 5
OP_GET = 6

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
   return (rc == 0, rc, variables)

def from_exception(exc):
   if exc.error_code is None: 
      exc.error_code = 0
   if exc.additional_data is None:
      exc.additional_data = 0
   return (exc.error_code == 0, exc.error_code, exc.additional_data)


def success(variables=0):
   if variables is None:
      variables = 0 # (paranoid?) prevent XMLRPC marshalling errors
   return (True, ERR_SUCCESS, variables)

