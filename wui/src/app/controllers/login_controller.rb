require "util/codes"

# the login controller is what the app users get when there is no valid token in the @session variable.
# it should be the only controller in the application derived from ApplicationControllerUnlocked, all
# others, being Locked, require a token.  Should this be changed to derive from a Locked controller, you'll
# get an infinite reload to this page.

class LoginController < ApplicationControllerUnlocked

   def index
      # accessing any element in this controller other than input or submit goes to "input"
      redirect_to :action => "input"
   end

   def input
      # this is just a form.  No need for database loads yet.
   end


   def submit
      f_username = @params["form"]["username"]
      f_password = @params["form"]["password"]

      # check on authentication via XMLRPC.  
      # FIXME: this really needs to be https in the future.
      begin 
          (rc, results) = @@server.call("user_login",f_username,f_password)
      rescue Errno::ECONNREFUSED
          @flash[:notice] = "Could not connect to ShadowManager server."
          redirect_to :action => "input"
          return
      end

      if rc != 0
          # FIXME: look up error codes in string table
          @flash[:notice] = "Login failed (#{ERRORS[rc]})."
          # ask the user to input the fields again 
          # (the right error messages will show up on redirect because of @flash)
          redirect_to :action => "input"
          return
      else
          # login was successful, so store the session token, which is needed for all
          # future RPC calls, in @session.
          @session[:login] = results["data"]
          # go to the user/list page on default login.  
          # FIXME:  this isn't a super-compelling page to go to, we eventually would want
          # something more "dashboard" like, or at least "Welcome to Shadowmanager" like.
          redirect_to :controller => 'user', :action => 'list'
          return
      end
   end

end
