class UserController < ApplicationController
   include ApplicationHelper
   
   def index
       redirect_to :action => 'list'
   end

   def list
       ApplicationHelper.require_auth()
       # FIXME: read from WS.
       @items = []
   end

   def logout
       @session[:login] = nil
       redirect_to :controller => "login", :action => "index"
   end

   def add
       ApplicationHelper.require_auth()
   end

   def add_submit
       ApplicationHelper.require_auth()
   end

   def delete
       ApplicationHelper.require_auth()
   end

   def delete_submit
       ApplicationHelper.require_auth()
   end

   def viewedit
       ApplicationHelper.require_auth()
   end

   def viewedit_submit
       ApplicationHelper.require_auth()
   end


end
