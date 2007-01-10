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
       @deployments = ManagedObject.retrieve_all(Deployment, @session).collect do |entry|
           [ entry.id, entry.id ]
       end
       @machines = ManagedObject.retrieve_all(Machine, @session).collect do |entry|
           [ entry.name, entry.id ]
       end
       @images = ManagedObject.retrieve_all(Image, @session).collect do |entry|
           [ entry.name, entry.id ]
       end
       @users = ManagedObject.retrieve_all(User, @session).collect do |entry|
           [ entry.username, entry.id ]
       end
       @states = []
       @operations = []
       @deployments.insert(0,EMPTY_ENTRY)
       @machines.insert(0,EMPTY_ENTRY)
       @images.insert(0,EMPTY_ENTRY)
       @users.insert(0,EMPTY_ENTRY)

       # FIXME: finish
    end
end
