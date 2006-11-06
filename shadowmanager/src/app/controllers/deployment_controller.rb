require 'xmlrpc/client'
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class DeploymentController < ApplicationController
   include ApplicationHelper
   
   def index
       redirect_to :action => 'list'
   end

   def list
       ApplicationHelper.require_auth()
       @items = @@server.call("get_deployments")
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
