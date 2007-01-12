# Methods added to this helper will be available to all templates in the application.

require 'rubygems'
require_gem 'rails'
require 'erb'

module ApplicationHelper

   # mapping between primary/secondary menu items
   # and controller/action pages.  
   # this allows for generation of menus via the menubar calls also in this helper.
   @NAVIGATION = [
      [ "machine"    , [ "list", "edit" ] ],
      # FIXME: production will have no image add in the menu (remote it later)
      [ "image"      , [ "list", "edit" ] ],
      [ "deployment" , [ "list", "edit" ] ],
      # FIXME: production will have no task add in the menu (remove it later)
      [ "task"       , [ "list", "edit" ] ],
      [ "user"       , [ "list", "edit", "logout" ] ]
   ]

   # FIXME: use better stringification, plans for i18n can come later
   # mapping of URL components to (English) display names.
   @STRINGS = {
       "machine"    => "Machines",
       "edit"       => "Add",
       "list"       => "List",
       "deployment" => "Virtual Image Deployments",
       "user"       => "Users",
       "logout"     => "Logout",
       "image"      => "Image Profiles",
       "task"       => "Task Queue"
   }

   # this renders both the top and bottom menubar.  A call to this menubar function 
   # must be made in every template (rhtml) file in this application that needs to render
   # navigation.  The template must pass in the first parameter that corresponds to the controller
   # name (ex: machine) and a second parameter that corresponds to a controller action (ex: list).
   # these parameters tell the menu which items to indicate as selected.  Selected links will not be clickable
   # but will appear more prominent and bold-like so folks can tell where they are in the navigation hierarchy.

   def ApplicationHelper.menubar(primary,secondary)
       html = ApplicationHelper.top_menubar(primary)
       html += ApplicationHelper.bottom_menubar(primary,secondary)
       return "<DIV ID='navigation'>" + html + "</DIV>"
   end

   # the top half of the menubar, corresponding to the controller portions (i.e. image, machine, deployment, etc) 

   def ApplicationHelper.top_menubar(primary)
       template = <<-EOF
              <DIV ID="primary_menu">
                  <TABLE>
                      <TR>
                         <% @NAVIGATION.each do |con| %>
                            <TD>
                            <% if con[0] == primary %>
                               <SPAN ID="primary_menu_selected">
                                  <%= @STRINGS[primary] %>
                               </SPAN>
                            <% else %>
                               <SPAN ID="primary_menu_unselected">
                                  <%= "<A HREF='../../" + con[0] + "/list'>" + @STRINGS[con[0]] + "</A>" %>
                               </SPAN>
                            <% end %>
                            </TD>
                         <% end %>
                      </TR>
                 </TABLE>
             </DIV>
       EOF
       return ERB.new(template, 0, '%').result(binding)
   end

   # the bottom half of the menubar, corresponding to controller actions (edit, list, etc)

   def ApplicationHelper.bottom_menubar(primary,secondary)
       items = @NAVIGATION.find { |a| a[0] == primary }[1]
       template = <<-EOF
              <DIV ID="secondary_menu">
                  <TABLE>
                      <TR>
                         <% items.each do |second| %>
                            <TD>
                            <% if secondary == second %>
                               <!-- <%= secondary %> | <%= second %> -->
                               <SPAN ID="secondary_menu_selected">
                                  <%= @STRINGS[second] %>
                               </SPAN>
                            <% else %>
                               <SPAN ID="secondary_menu_unselected">
                                  <%= "<A HREF='../../#{primary}/" + second + "'>" + @STRINGS[second] + "</A>" %>
                               </SPAN>
                            <% end %>
                            </TD>
                         <% end %>
                      </TR>
                 </TABLE>
              </DIV>
       EOF
       return ERB.new(template,0,'%').result(binding)
   end


end
