
class LoginController < ApplicationControllerUnlocked

   def index
      redirect_to :action => "input"
   end

   def input
      # this is just a form.  No need for database loads yet.
   end

   def submit
      f_username = @params["form"]["username"]
      f_password = @params["form"]["password"]
      (success, rc, token) = @@server.call("user_login",f_username,f_password)
      if not success
          # FIXME: look up error codes in string table
          @flash[:notice] = "Login failed (#{rc})."
          redirect_to :action => "input"
          return
      else
          @session[:login] = token
          redirect_to :controller => 'user', :action => 'list'
          return
      end
   end

end
