require 'xmlrpc/client'
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class UserController < ApplicationController
   include ApplicationHelper
   
   def index
       redirect_to :action => 'list'
   end

   def list
       @items = @@server.call("user_list")
   end

   def logout
       @session[:login] = nil
       redirect_to :controller => "login", :action => "index"
   end

   def add
   end

   def add_submit
      results = @@server.call("user_add", @params["form"])
      if not results
          @flash[:notice] = "User creation failed."
          redirect_to :action => "input"
          return
      else
          @flash[:notice] = "User #{@params["form"]["username"]} created: #{results}."
          redirect_to :action => 'list'
          return
      end
   end

   def delete
       # FIXME: make WS call to perform actual delete here.  Right here, actually.
       # and show an appropriate message in flash.
       results = @@server.call("user_delete", @params[:id])
       @flash[:notice] = "Deleted user #{@params[:id]}"
       if not results
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
