require 'xmlrpc/client'
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class UserController < ApplicationController
   include ApplicationHelper
   
   def index
       redirect_to :action => 'list'
   end

   def list
       @items = @@server.call("user_list").collect {|hash| User.new(hash)}
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

   def edit
       @item = User.new(@@server.call("user_get", @params[:id]))
   end

   def edit_submit
      results = @@server.call("user_edit", @params["form"])
      if not results
          @flash[:notice] = "User edit failed."
          redirect_to :action => "input"
          return
      else
          @flash[:notice] = "User #{@params["form"]["username"]} modified: #{results}."
          redirect_to :action => 'list'
          return
      end
   end

   def delete
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

   class User
       attr_reader :id, :username, :password, :first, :middle, :last, :description, :email
       attr_writer :id, :username, :password, :first, :middle, :last, :description, :email

       def initialize(hash)
           @id = hash["id"]
           @username = hash["username"]
           @password = hash["password"]
           @first = hash["first"]
           @middle = hash["middle"]
           @last = hash["last"]
           @description = hash["description"]
           @email = hash["email"]
       end
   end
end
