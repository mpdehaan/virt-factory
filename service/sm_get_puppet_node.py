#!/usr/bin/python
"""
Utility script which provides a list of puppet classes to puppetmasterd for a given node.

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

import sys
import string

from modules import puppet
from codes import *

#--------------------------------------------------------------------------
      
def main(argv):
    """
    Start things up.
    """
    if len(argv) == 2:
        puppet_obj = puppet.Puppet()
        puppet_node_return = puppet_obj.node_info(None, {"nodename": argv[1]})
        if (puppet_node_return.error_code != ERR_SUCCESS):
            sys.exit(1)

        if "parent" in puppet_node_return.data:
            print puppet_node_return.data["parent"]
        else:
            print
        print " ".join(puppet_node_return.data["puppet_classes"])
    else:
        print "Usage:" 
        print "sm_get_puppet_node.py nodename"
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)


