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

# the virt-factory WUI automatically converts return codes that represent failure into Ruby exception
# objects -- XMLRPCClientExceptions.  These exceptions split out meaningful data out of the return and
# know how to explain themselves, on screen in the html page, to the user.

class XMLRPCClientException < Exception

    # the return code format for all virt-factory methods is of the form (integer, hash) where
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

    def initialize(return_code, raw_data, attempted_obj = nil)

        # direct return values from service
        @return_code = return_code
        @raw_data    = raw_data
  
        # for convience, rip certain data out of the hash
        @job_id         = raw_data["job_id"]
        @invalid_fields = raw_data["invalid_fields"] 
        @data           = raw_data["data"]
        @comment        = raw_data["comment"]
        @stacktrace     = raw_data["stacktrace"]

        # note that data and job_id are pretty much always 
        # going to be null, so we'll ignore them when producing
        # the human readable representation of the error occurance.

    end    

    # produce a string suitable for inclusion in a floating error DIV or the right callout,
    # that explains what went wrong with the last operation.  It should be human readable
    # and as understandable as possible.

    def get_human_readable()
        how = ERRORS[@return_code] # from util/codes.rb
        basics = "Operation failed, #{how}."
        
        if @invalid_fields then
           basics = basics + "<br/>"
           # FIXME: TODO: also show reasons
           basics = "The following fields were invalid:"
           @invalid_fields.each do |key, reason|  
              basics = basics + "<br/>" + key + ": " + reason
           end
        end

        if @stacktrace then
           basics = basics + "<br/>"
           basics = basics + "Stacktrace: #{@stacktrace}"
        end        
 
        if @comment then
           basics = basics + "<br/>"
           basics = basics + "Additional info: #{@comment}"
        end

        return basics
 

    end

end

class ApplicationController < ActionController::Base

    init_gettext "ump"

    before_filter :login_required
    layout "virt-factory-layout"

    def login_required
        unless session[:login]
            redirect_to :controller => "login", :action => "input"
            return false
        end
        begin
            (rc, data) = @@server.call("token_check", session[:login])

        rescue RuntimeError
            # internal server error (500) likely here if connection to web svc was
            # severed by a restart of the web service during development.
            flash[:notice] = _("Internal Server Error")
            redirect_to :controller => "login", :action => "input"
            return false 
        end
        unless rc == ERR_SUCCESS
            # token has timed out, so redirect here and get a new one
            # rather than having to do a lot of duplicate error handling in other places
            flash[:notice] = _("Session timeout (#{ERRORS[rc]}).")
            stacktrace = data["stacktrace"]
            flash[:errmsg] = stacktrace if stacktrace
            redirect_to :controller => "login", :action => "input"
            return false
        end
    end
end

# FIXME do something with the return data upon error (could be an error message or traceback
class ApplicationControllerUnlocked < ActionController::Base
    layout "virt-factory-layout"

end

