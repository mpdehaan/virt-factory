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

class TagController < AbstractObjectController

   def object_class
       Tag
   end

   def edit
        super
        @machines = ManagedObject.retrieve_all(Machine, get_login)
        @deployments = ManagedObject.retrieve_all(Deployment, get_login)
    end

    def edit_submit
        params["form"]["machine_ids"] = [] if params["form"]["machine_ids"].nil?
        params["form"]["deployment_ids"] = [] if params["form"]["deployment_ids"].nil?
        super
    end

    def remove_machine
        args = { "id" => params[:machine_id], "tag_id" => params[:id]}
        begin
            ManagedObject.call_server("machine_remove_tag", get_login, args)
        rescue XMLRPCClientException => ex
            set_flash_on_exception(ex)
        end
        redirect_to :action=> "edit", :id => params[:id]
    end

    def remove_deployment
        args = { "id" => params[:deployment_id], "tag_id" => params[:id]}
        begin
            ManagedObject.call_server("deployment_remove_tag", get_login, args)
        rescue XMLRPCClientException => ex
            set_flash_on_exception(ex)
        end
        redirect_to :action=> "edit", :id => params[:id]
    end


end
