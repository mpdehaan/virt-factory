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

import sys

# used for specifying types of validation required, and so forth.
# internal to python code and of no concern to clients of the service.

OP_ADD = 1
OP_EDIT = 2
OP_DELETE = 3
OP_LIST = 4
OP_METHOD = 5
OP_GET = 6

# error codes for the web service.
# FIXME: eventually __main__ will autogenerate a Ruby version

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
ERR_UNCAUGHT = 999

ARCH_X86 = 0
ARCH_X86_64 = 1
ARCH_IA64 = 2

MACHINE_TYPE_BAREMETAL_APPLIANCE = 0
MACHINE_TYPE_APPLIANCE_CONTAINER = 1

IMAGE_TYPE_VIRT_APPLIANCE = 1
IMAGE_TYPE_BAREMETAL_APPLIANCE = 2
IMAGE_TYPE_EITHER_APPLIANCE = 3
IMAGE_TYPE_APPLIANCE_CONTAINER = 4

def result(rc, variables=[]):
   return (rc, variables)

def from_exception(exc):
   if exc.error_code is None: 
      exc.error_code = 0
   if exc.additional_data is None:
      exc.additional_data = 0
   return (exc.error_code, exc.additional_data)


def success(variables=0):
   if variables is None:
      variables = 0 # (paranoid?) prevent XMLRPC marshalling errors
   return (ERR_SUCCESS, variables)

if __name__ == "__main__":
   module = sys.modules[__name__]
   for x in sorted(module.__dict__.keys()):
       obj = module.__dict__[x]
       if type(obj) == int:
           print "%s = %s" % (x, obj)
