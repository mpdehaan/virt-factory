# Methods added to this helper will be available to all templates in the application.
module ApplicationHelper

   def require_permission(feature)
      # FIXME: actually pay attention to feature input
      unless @session[:login]
         redirect_to :controller => "login", :action => "input"
      end
   end

end
