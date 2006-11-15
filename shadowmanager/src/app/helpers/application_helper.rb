# Methods added to this helper will be available to all templates in the application.

require 'rubygems'
require_gem 'rails'
require 'erb'

module ApplicationHelper

   # mapping between primary/secondary menu items
   # and controller/action pages
   @NAVIGATION = [
      [ "machine" , [ "list", "edit" ] ],
      [ "image" , [ "list", "edit" ] ],
      [ "deployment" , [ "list", "edit" ] ],
      [ "user" , [ "list", "edit", "logout" ] ]
   ]

   # FIXME: use better stringification
   @STRINGS = {
       "machine" => "Machines",
       "edit" => "Add",
       "list" => "List",
       "deployment" => "Deployments",
       "user" => "Users",
       "logout" => "Logout",
       "image" => "Images"
   }

   def ApplicationHelper.menubar(primary,secondary)
       html = ApplicationHelper.top_menubar(primary)
       html += ApplicationHelper.bottom_menubar(primary,secondary)
       return "<DIV ID='navigation'>" + html + "</DIV>"
   end

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

   def ApplicationHelper.bottom_menubar(primary,secondary)
       items = @NAVIGATION.find { |a| a[0] == primary }[1]
       template = <<-EOF
              <DIV ID="secondary_menu">
                  <TABLE>
                      <TR>
                         <% items.each do |second| %>
                            <TD>
                            <% if secondary == second %>
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
