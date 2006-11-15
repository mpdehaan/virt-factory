require 'xmlrpc/client'
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class UserController < ApplicationController
   include ApplicationHelper
   
   def index
       redirect_to :action => 'list'
   end

   def list
       (success, rc, results) = @@server.call("user_list",@session[:login])
       if not success
           @items = []
           @flash[:notice] = "Error: No users found (#{rc})."
       else
           @items = results.collect {|hash| User.new(hash)}
       end
   end

   def logout
       @session[:login] = nil
       redirect_to :controller => "login", :action => "index"
   end

   def add
   end

   def add_submit
      (success, rc, data) = @@server.call("user_add", @session[:login], @params["form"])
      if not success
          @flash[:notice] = "User creation failed #{rc}."
          redirect_to :action => "input"
          return
      else
          @flash[:notice] = "User #{@params["form"]["username"]} created: #{results}."
          redirect_to :action => 'list'
          return
      end
   end

   def edit
       # FIXME: error handling on "success"
       (success, rc, User.new(@item)) = @@server.call("user_get", @session[:login], @params[:id]) 
   end

   def edit_submit
      (success, rc, data) = @@server.call("user_edit", @session[:login], @params["form"])
      if not success
          @flash[:notice] = "User edit failed (#{rc})."
          redirect_to :action => "input"
          return
      else
          @flash[:notice] = "User #{@params["form"]["username"]} modified."
          redirect_to :action => 'list'
          return
      end
   end

   def delete
       (success, rc, data) = @@server.call("user_delete", @session[:login], @params[:id])
       @flash[:notice] = "Deleted user #{@params[:id]}"
       if not success
          @flash[:notice] = "User #{@params[:id]} deletion failed (#{rc})"
       else
          @flash[:notice] = "User #{@params[:id]} deleted."
       end
       redirect_to :action => "list"
       return
   end

   def viewedit
   end

   def viewedit_submit
   end

   class User
       attr_accessor :id, :username, :password, :first, :middle, :last, :description, :email

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
