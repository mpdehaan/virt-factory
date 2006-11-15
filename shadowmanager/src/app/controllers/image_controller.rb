require 'xmlrpc/client'
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class ImageController < ApplicationController
   include ApplicationHelper
   
   def index
       redirect_to :action => 'list'
   end

   def list
       (success, rc, @items) = @@server.call("image_list",@session[:login])
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
