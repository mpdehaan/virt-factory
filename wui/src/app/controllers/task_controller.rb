# Copyright 2007, Red Hat Inc
# Michael DeHaan <mdehaan@redhat.com> 
# Scott Seago <sseago@redhat.com>
#
#
# This software may be freely redistributed under the terms of the GNU
# general public license.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


# the task controller deals with background actions, some of which the user might be interested
# in watching from the UI.  It should show state but allow only a minimum of editing (possibly
# pausing a task) and that's it.
#
# the backend actually uses "action" for the word "task", but the word ActionController is 
# apparently reserved by Rails.

class TaskController < AbstractObjectController

   def object_class
       Task
   end

   def edit
       # allows adding or changing a task (state only), depending on how invoked
       # NOTE: this is mainly for development purposes, we probably won't allow this directly once released
       # may be good to have the list though.
       super
       @users = ManagedObject.retrieve_all(User, @session).collect do |entry|
           [ entry.username, entry.id ]
       end
       # FIXME: for consistancy this should be in codes-lookup.rb
       @states = [ 
           [ "Queued",   TASK_STATE_QUEUED   ],
           [ "Running",  TASK_STATE_RUNNING  ],
           [ "Paused",   TASK_STATE_PAUSED   ],
           [ "Failed",   TASK_STATE_FAILED   ],
           [ "Finished", TASK_STATE_FINISHED ]
       ]
       @operations = [ 
           [ "Sync Provisioning",            TASK_OPERATION_COBBLER_SYNC  ],
           [ "Install Baremetal System",     TASK_OPERATION_INSTALL_METAL ],
           [ "Install Virtualized System",   TASK_OPERATION_INSTALL_VIRT  ],
           [ "Sync Recipes",                 TASK_OPERATION_PUPPET_SYNC   ]
       ]
       @users.insert(0,EMPTY_ENTRY)

       # FIXME: finish
    end
end
