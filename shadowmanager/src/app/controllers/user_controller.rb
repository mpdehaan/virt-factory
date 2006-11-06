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
   end

   def delete
       # FIXME: make WS call to perform actual delete here.  Right here, actually.
       # and show an appropriate message in flash.
       @flash[:notice] = "We pretended to delete user #{@params[:id]}"
       redirect_to :controller => "user", :action => "list"
   end

   def viewedit
   end

   def viewedit_submit
   end


end
