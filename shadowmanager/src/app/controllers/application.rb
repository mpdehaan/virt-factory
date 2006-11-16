require "xmlrpc/client"
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class ApplicationController < ActionController::Base

   before_filter :login_required
   layout "shadowmanager-layout"

   def login_required
      unless @session[:login]
         redirect_to :controller => "login", :action => "input"
         return false
      end
      begin
         (success, rc, data) = @@server.call("token_check", @session[:login])
      rescue RuntimeError
         # internal server error (500) likely here if connection to web svc was
         # severed by a restart of the web service during development.
         redirect_to :controller => "login", :action => "input"
         return false 
      end
      unless success
         # token has timed out, so redirect here and get a new one
         # rather than having to do a lot of duplicate error handling in other places
         @flash[:notice] = "Session timeout (#{rc})."
         redirect_to :controller => "login", :action => "input"
         return false
      end
   end

end

class ApplicationControllerUnlocked < ActionController::Base
   layout "shadowmanager-layout"

end


