require "util/codes"
require "util/code-lookup"
require "xmlrpc/client"
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class XMLRPCClientException < Exception
    attr_accessor :notice, :errmsg
    def initialize(notice, result)
        @rc = notice
        @result = result
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
