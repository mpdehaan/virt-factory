class DeploymentController < ApplicationController
   include ApplicationHelper
   
   def index
       redirect_to :action => 'list'
   end

   def list
       ApplicationHelper.require_auth()
       # FIXME: read from WS.
       @items = []
   end

end
