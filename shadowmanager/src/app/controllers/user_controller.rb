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

end
