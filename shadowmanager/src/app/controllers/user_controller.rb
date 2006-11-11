require 'xmlrpc/client'
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class UserController < ApplicationController
   include ApplicationHelper
   
   def index
       redirect_to :action => 'list'
   end

   def list
       @items = @@server.call("get_users")
   end

   def logout
       @session[:login] = nil
       redirect_to :controller => "login", :action => "index"
   end

   def add
   end

   def add_submit
      f_username = @params["form"]["username"]
      f_password = @params["form"]["password"]
      f_first = @params["form"]["first"]
      f_middle = @params["form"]["middle"]
      f_last = @params["form"]["last"]
      f_description = @params["form"]["description"]
      f_email = @params["form"]["email"]
      results = @@server.call("add_user", f_username, f_password, f_first, 
                           f_middle, f_last, f_description, f_email)
      if  results.nil? or (results == -1)
          @flash[:notice] = "User creation failed."
          redirect_to :action => "input"
          return
      else
          @flash[:notice] = "User #{f_username} created: #{results}."
          redirect_to :action => 'list'
          return
      end
   end

   def delete
       # FIXME: make WS call to perform actual delete here.  Right here, actually.
       # and show an appropriate message in flash.
       results = @@server.call("delete_user", @params[:id])
       @flash[:notice] = "Deleted user #{@params[:id]}"
       if  results.nil? or (results == -1)
          @flash[:notice] = "User #{@params[:id]} deletion failed.  #{results}"
       else
           @flash[:notice] = "User #{@params[:id]} deleted: #{results}., #{results.class}"
       end
       redirect_to :action => "list"
       return
   end

   def viewedit
   end

   def viewedit_submit
   end


end
