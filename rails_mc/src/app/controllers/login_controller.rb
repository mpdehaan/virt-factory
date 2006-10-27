class LoginController < ApplicationController

   def index
      redirect_to :action => "input"
   end

   def input
   end

   def submit
      f_username = @params["form"]["username"]
      f_password = @params["form"]["password"]
      puts ",#{f_username},"
      puts ",#{f_password},"
      item = User.find_by_username(f_username)
      if item.nil?
          print "is nil"
          redirect_to :action => "input"
          return
      end
      puts item
      puts item.password
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
