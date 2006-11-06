# Methods added to this helper will be available to all templates in the application.

require 'rubygems'
require_gem 'rails'

module ApplicationHelper

   # mapping between primary/secondary menu items
   # and controller/action pages
   @NAVIGATION = [
      [ "demo" , [ "list" ] ],
      [ "machine" , [ "list", "add" ] ],
      [ "image" , [ "list", "add" ] ],
      [ "deployment" , [ "list", "add" ] ],
      [ "user" , [ "logout" ] ]
   ]

   # FIXME: use better stringification
   @STRINGS = {
       "machines" => "Machines",
       "demo" => "Demo",
       "add" => "Add",
       "list" => "List",
       "deployments" => "Deployments",
       "user" => "User",
       "logout" => "Logout",
       "images" => "Images"
   }

   def ApplicationHelper.require_auth()
      unless @session.nil? or @session[:login]
         redirect_to :controller => "login", :action => "input"
      end
   end

   def ApplicationHelper.menubar(primary,secondary)
       # shortcut, as we always want a permission check whenever
       # we display a menu bar.
       html = "<DIV ID='menus'>"
       html += "<DIV ID='primary_menu'><TABLE><TR><TD>"
       # draw top menubar, with links to all but the active category
       @NAVIGATION.each do |toplevel|
           html += "<TD>"
           if primary == toplevel[0]
              html += primary
           else
              puts toplevel[0]
              html += "<A HREF='../../#{toplevel[0]}/index'>#{toplevel[0]}</A>"
           end
           html += "</TD>" 
       end
       html += "</TR></TABLE></DIV>"
       html += "<DIV ID='secondary_menu'><TABLE><TR>"
       # draw bottom menubar, with links to all but the active action
       @NAVIGATION.each do |toplevel|
           if toplevel[0] == primary
               toplevel[1].each do |secondlevel|
                   html += "<TD>"
                   if secondlevel == secondary
                      html += secondary
                   else
                      puts primary
                      puts secondary
                      html += "<A HREF='../../#{primary}/#{secondary}'>#{secondary}</A>"
                   end
                   html += "</TD>"
               end
               break
           end
       end
       html += "</TR></TABLE></DIV>"
       html += "</DIV>
       return html
   end

end
