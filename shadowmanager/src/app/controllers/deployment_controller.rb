require 'xmlrpc/client'
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class DeploymentController < ApplicationController
   include ApplicationHelper
   
   def index
       redirect_to :action => 'list'
   end

   def list
       @items = @@server.call("deployment_list")
   end

   def add
   end

   def add_submit
   end

   def delete
   end

   def viewedit
   end

   def viewedit_submit
   end


end
