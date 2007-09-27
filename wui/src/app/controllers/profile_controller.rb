# Copyright 2006-2007, Red Hat, Inc
# Scott Seago <sseago@redhat.com>
# Michael DeHaan <mdehaan@redhat.com>
# 
# This software may be freely redistributed under the terms of the GNU
# general public license.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

# Profiles are either virtual or bare metal appliance profiles that can be provisioned to machines (dom0 containers and 
# bare metal appliances) or deployed with a Deployment entry (domU's).

require "xmlrpc/base64"
 
class ProfileController < AbstractObjectController

    def edit
        # the profile edit box needs to allow picking, via drop down, all of the values for possible distributions.
        #---
        # NOTE: in the future, it may be that certain profiles are incompatible with certain distributions, but let's
        # fight that when we come to it.
        #+++
        super
        @distributions = ManagedObject.retrieve_all(Distribution, get_login).collect do |dist|
            [dist.name, dist.id]
        end
        # the list needs to start off with no selection in the GUI.
        @distributions.insert(0,EMPTY_ENTRY)
    end

    def object_class
        Profile
    end

    def upload_submit
        file = params[:rpm_file]
        begin
            ManagedObject.call_server("profile_import_from_upload", get_login, 
	                              { "file" => XMLRPC::Base64.new(file.read),
				        "filename" => file.original_filename,
                                        "force" => true}, file.original_filename)
            flash[:notice] = _("Imported profile #{file.original_filename}")
        rescue XMLRPCClientException => ex
            set_flash_on_exception(ex)
        end
        redirect_to :action => "list"
    end

    def url_import_submit
        form = params[:form]
        url = form[:profile_url]
	print "URL is: ", url
        begin
            ManagedObject.call_server("profile_import_from_url", get_login, 
	                              { "url" => url,
                                        "force" => true}, url)
            flash[:notice] = _("Imported profile #{url}")
        rescue XMLRPCClientException => ex
            set_flash_on_exception(ex)
        end
        redirect_to :action => "list"
    end

end

