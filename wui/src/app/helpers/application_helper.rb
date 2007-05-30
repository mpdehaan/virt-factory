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
       <li><strong><%= _("Machines") %></strong>
	   <ul>
	   <li><A HREF="#{app_root}/machine/list"><%= _("View Machines") %></A></li>
	   <li><A HREF="#{app_root}/machine/edit"><%= _("Add a Machine via PXE") %></A></li>
	   <li><A HREF="#{app_root}/regtoken/edit"><%= _("Create Registration Tokens") %></A></li>
	   <li><A HREF="#{app_root}/regtoken/list"><%= _("View Registration Tokens") %></A></li>
	   </ul>
       </li>
       <li><strong><%= _("Image Profiles") %></strong>
	   <ul>
	   <li><A HREF="#{app_root}/profile/list"><%= _("View Image Profiles") %></A></li>
	   </ul>
       </li>
       <li><strong><%= _("Virtual Deployments") %></strong>
           <ul>
           <li><A HREF="#{app_root}/deployment/list"><%= _("View Virtual Deployments") %></A></li>
           <li><A HREF="#{app_root}/deployment/edit"><%= _("Add a Virtual Deployment") %></A></li>
           </ul>
       </li>
       <li><strong><%= _("Task Queue") %></strong>
           <ul>
           <li><A HREF="#{app_root}/task/list"><%= _("View Task Queue") %></A></li>
           </ul>
       </li>
       <li><strong><%= _("Users") %></strong>
           <ul>
           <li><A HREF="#{app_root}/user/list"><%= _("View virt-factory Users") %></A></li>
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
