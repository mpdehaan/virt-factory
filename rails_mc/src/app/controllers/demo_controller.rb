
class DemoController < ApplicationController

   include ApplicationHelper

   def index
      redirect_to :action => 'list'
   end

   def list
      require_permission(0)
      @items = ["audit","event","deployment","deployment_value",
                "event","feature","field_type","image","image_value",
                "machine","machine_value","metric","permission",
                "role","user"].sort
   end

end
