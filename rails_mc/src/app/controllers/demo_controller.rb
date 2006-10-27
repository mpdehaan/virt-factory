class DemoController < ApplicationController

   def index
      redirect_to :action => 'list'
   end

   def list
      unless @session[:login]
         redirect_to :controller=>"login", :action=>"input"
      end
      @items = ["audit","event","deployment","deployment_value",
                "event","feature","field_type","image","image_value",
                "machine","machine_value","metric","permission",
                "role","user"].sort
   end

end
