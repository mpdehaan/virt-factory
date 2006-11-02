require "xmlrpc/client"
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class LoginController < ApplicationController

   def index
      redirect_to :action => "input"
   end

   def input
      # this is just a form.  No need for database loads yet.
   end

   def submit
      f_username = @params["form"]["username"]
      f_password = @params["form"]["password"]
      item = @@server.call("login",f_username,f_password)
      if item.nil? or item < 0
          redirect_to :action => "input"
          return
      else
          @session[:login] = item.id
          redirect_to :controller => 'demo', :action => 'list'
          return
      end
   end

end
