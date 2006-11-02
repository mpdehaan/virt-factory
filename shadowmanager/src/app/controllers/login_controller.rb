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
      item = User.find_by_username(f_username)
      if item.nil?
          redirect_to :action => "input"
          return
      end
      if item.password == f_password
          @session[:login] = f_username
          redirect_to :controller => "demo", :action => "list"
          return
      else
          redirect_to :action => "input"
          return
      end
   end

end
