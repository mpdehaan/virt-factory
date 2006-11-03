
class DemoController < ApplicationController

   include ApplicationHelper

   def index
      redirect_to :action => 'list'
   end

   def list
      require_permission(0)
      @items = ["audit","event","deployment",
                "event","feature","image",
                "machine","metric", "user"].sort
   end

end
