
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
           @items = results.collect {|hash| User.from_hash(hash)}
       end
   end

   def logout
       @session[:login] = nil
       redirect_to :controller => "login", :action => "index"
   end

   def edit
       # FIXME: error handling on "success"
       if @params[:id].nil?
           @item = User.new
           @operation = "Add"
       else
           plist = { "id" => @params[:id] } 
           (success, rc, item_hash) = @@server.call("user_get", @session[:login], plist)
           @item = User.from_hash(item_hash)
           @operation = "Edit"
       end
   end

   def edit_submit
       id = @params["form"]["id"]
       if id.nil? || id.empty?
           operation = "add"
       else
           operation = "edit"
       end
       print "#{operation}, id: #{@params["form"]["id"]} #{@params["form"]["id"].class} \n" 
       (success, rc, data) = @@server.call("user_#{operation}", @session[:login], @params["form"])
       if not success
           @flash[:notice] = "User #{operation} failed (#{rc})."
          redirect_to :action => "edit"
          return
      else
           @flash[:notice] = "User #{@params["form"]["username"]} #{operation} succeeded."
           redirect_to :action => 'list'
           return
       end
   end

   def delete
       plist = { "id" => @params[:id] } 
       (success, rc, data) = @@server.call("user_delete", @session[:login], plist)
       if not success
          @flash[:notice] = "User #{@params[:id]} deletion failed (#{rc})"
       else
          @flash[:notice] = "User #{@params[:id]} deleted (#{success},#{rc},#{data})."
       end
       redirect_to :action => "list"
       return
   end

   def viewedit
   end

   def viewedit_submit
   end

   class User
       ATTR_LIST = [:id, :username, :password, :first, :middle, :last, :description, :email]
       ATTR_LIST.each {|x| attr_accessor x}

       def self.from_hash(hash)
           user = User.new
           ATTR_LIST.each { |attr| user.method(attr.to_s+"=").call(hash[attr.to_s]) }
           user
       end
       def to_hash
           hash = Hash.new
           ATTR_LIST.each { |attr| hash[attr.to_s] = self.method(attr).call }
           hash
       end
   end
end
