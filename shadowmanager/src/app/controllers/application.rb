
class ApplicationController < ActionController::Base

   before_filter :login_required
   layout "shadowmanager-layout"

   def login_required
      unless @session[:login]
         redirect_to :controller => "login", :action => "input"
         return false
      end
   end

end

class ApplicationControllerUnlocked < ActionController::Base
   layout "shadowmanager-layout"

end
