# Methods added to this helper will be available to all templates in the application.

require 'rubygems'
gem 'rails'
require 'erb'

module ApplicationHelper

   def ApplicationHelper.menubar(primary,secondary)
       # FIXME: primary and secondary are no longer used.
       # should change method signature.
       app_root = ActionController::AbstractRequest.relative_url_root
       template = <<-EOF
       <ul class="nav">
       <li><strong><%= _("Hosts") %></strong>
	   <ul>
	   <li><A HREF="#{app_root}/machine/list"><%= _("View Hosts") %></A></li>
	   <li><A HREF="#{app_root}/machine/edit"><%= _("Add a Host via PXE") %></A></li>
	   <!-- not needed under current auth mechanism
           <li><A HREF="#{app_root}/regtoken/edit"><%= _("Create Registration Tokens") %></A></li>
	   <li><A HREF="#{app_root}/regtoken/list"><%= _("View Registration Tokens") %></A></li>
	   -->
           </ul>
       </li>
       <li><strong><%= _("Profiles") %></strong>
	   <ul>
	   <li><A HREF="#{app_root}/profile/list"><%= _("View Profiles") %></A></li>
	   <li><A HREF="#{app_root}/profile/upload"><%= _("Add a Profile via file upload") %></A></li>
	   <li><A HREF="#{app_root}/profile/url_import"><%= _("Add a Profile via external URL") %></A></li>
	   </ul>
       </li>
       <li><strong><%= _("Guests") %></strong>
           <ul>
           <li><A HREF="#{app_root}/deployment/list"><%= _("View Guests") %></A></li>
           <li><A HREF="#{app_root}/deployment/edit"><%= _("Add a Guest") %></A></li>
           </ul>
       </li>
       <li><strong><%= _("Task Queue") %></strong>
           <ul>
           <li><A HREF="#{app_root}/task/list"><%= _("View Task Queue") %></A></li>
           </ul>
       </li>
       <li><strong><%= _("Tags") %></strong>
           <ul>
           <li><A HREF="#{app_root}/tag/list"><%= _("View Tags") %></A></li>
           </ul>
       </li>
       <li><strong><%= _("Users") %></strong>
           <ul>
           <li><A HREF="#{app_root}/user/list"><%= _("View Users") %></A></li>
           <li><A HREF="#{app_root}/user/edit"><%= _("Add a User") %></A></li>
           <li><A HREF="#{app_root}/user/logout"><%= _("Logout") %></A></li>
           </ul>
       </li>
       </ul>
       EOF

       html = ERB.new(template, 0, '%').result(binding)
       return "<DIV ID='navigation'>" + html + "</DIV>"


   end

end
