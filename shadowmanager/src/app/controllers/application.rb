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


require "util/codes"
require "util/code-lookup"
require "xmlrpc/client"
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class XMLRPCClientException < Exception

    # the return code format for all ShadowManager methods is of the form (integer, hash) where
    # hash can contain one or more of the following fields.  All fields are allowed to be missing.
    # the first integer is a return code, 0=success, other codes indicate failure.
    #
    # the raw datastructure is as follows:
    #
    # {
    #    "job_id"         : integer,                           #  spawned background task
    #    "stacktrace"     : string,                            #  python stacktrace for uncaught exception
    #    "invalid_fields" : {
    #         field_name : REASON_CODE,                        #  rejected fields and why they were rejected.
    #     },
    #     "data"          : datastructure, defined by method
    #     "comment"       : optional explanation
    # } 
    #
    #
    # all things from the web service return in this form, and are not, as such, true XMLRPC Faults.
    # the web service should not trigger XMLRPC Faults in any instance.

    # note: these have been changed from attr_accessor as we don't want them writeable
    # from outside the class.  

    # raw return values
    attr_reader :return_code 
    attr_reader :raw_data

    # derived values 
    attr_reader :job_id 
    attr_reader :invalid_fields
    attr_reader :data
    attr_reader :comment

    def initialize(return_code, raw_data)

        # direct return values from service
        @return_code = result_code
        @raw_data    = raw_data
  
        # for convience, rip certain data out of the hash
        @result         = nil
        @job_id         = nil
        @invalid_fields = nil
        @data           = nil
        @comment        = nil
        @result         = raw_data["result"]         if raw_data.has_key?("result")
        @job_id         = raw_data["job_id"]         if raw_data.has_key?("job_id")
        @invalid_fields = raw_data["invalid_fields"] if raw_data.has_key?("invalid_fields") 
        @data           = raw_data["data"]           if raw_data.has_key?("data")
        @comment        = raw_data["comment"]        if raw_data.has_key?("comment")
    end    
end

class ApplicationController < ActionController::Base

    before_filter :login_required
    layout "shadowmanager-layout"

    def login_required
        unless @session[:login]
            redirect_to :controller => "login", :action => "input"
            return false
        end
        begin
            (rc, data) = @@server.call("token_check", @session[:login])

        rescue RuntimeError
            # internal server error (500) likely here if connection to web svc was
            # severed by a restart of the web service during development.
            @flash[:notice] = "Internal Server Error"
            redirect_to :controller => "login", :action => "input"
            return false 
        end
        unless rc == ERR_SUCCESS
            # token has timed out, so redirect here and get a new one
            # rather than having to do a lot of duplicate error handling in other places
            @flash[:notice] = "Session timeout (#{ERRORS[rc]})."
            stacktrace = data["stacktrace"]
            @flash[:errmsg] = stacktrace if stacktrace
            redirect_to :controller => "login", :action => "input"
            return false
        end
    end
end

# FIXME do something with the return data upon error (could be an error message or traceback
class ApplicationControllerUnlocked < ActionController::Base
    layout "shadowmanager-layout"

end
