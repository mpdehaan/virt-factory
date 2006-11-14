require "xmlrpc/client"
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

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
      item = @@server.call("user_login",f_username,f_password)
      if not item
          @flash[:notice] = "Login failed."
          redirect_to :action => "input"
          return
      else
          @session[:login] = item.id
          redirect_to :controller => 'machine', :action => 'list'
          return
      end
   end

end
