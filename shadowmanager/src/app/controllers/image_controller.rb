class ImageController < ApplicationController
   include ApplicationHelper
   
   def index
       redirect_to :action => 'list'
   end

   def list
       @items = []
       # (success, rc, @items) = @@server.call("image_list",@session[:login])
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
