# Methods added to this helper will be available to all templates in the application.

require 'rubygems'
require_gem 'rails'
require 'erb'

module ApplicationHelper

   def ApplicationHelper.menubar(primary,secondary)
       # FIXME: primary and secondary are no longer used.
       # should change method signature.
       app_root = ActionController::AbstractRequest.relative_url_root
       template = <<-EOF
       <ul class="nav">
       <li><strong>Machines</strong>
	   <ul>
	   <li><A HREF="#{app_root}/machine/list">View Machines</A></li>
	   <li><A HREF="#{app_root}/machine/edit">Add a Machine via PXE</A></li>
	   <li><A HREF="#{app_root}/regtoken/edit">Create Registration Tokens</A></li>
	   <li><A HREF="#{app_root}/regtoken/list">View Registration Tokens</A></li>
	   </ul>
       </li>
       <li><strong>Image Profiles</strong>
	   <ul>
	   <li><A HREF="#{app_root}/profile/list">View Image Profiles</A></li>
	   <li><A HREF="#{app_root}/profile/edit">(Developers) Add an Image Profile</A></li>
	   </ul>
       </li>
       <li><strong>Virtual Deployments</strong>
           <ul>
           <li><A HREF="#{app_root}/deployment/list">View Virtual Deployments</A></li>
           <li><A HREF="#{app_root}/deployment/edit">Add a Virtual Deployment</A></li>
           </ul>
       </li>
       <li><strong>Task Queue</strong>
           <ul>
           <li><A HREF="#{app_root}/task/list">View Task Queue</A></li>
           <li><A HREF="#{app_root}/task/edit">Add a Task</A></A>
           </ul>
       </li>
       <li><strong>Users</strong>
           <ul>
           <li><A HREF="#{app_root}/user/list">View ShadowManager Users</A></li>
           <li><A HREF="#{app_root}/user/edit">Add a User</A></li>
           <li><A HREF="#{app_root}/user/logout">Logout</A></li>
           </ul>
       </li>
       </ul>
       EOF

       html = ERB.new(template, 0, '%').result(binding)
       return "<DIV ID='navigation'>" + html + "</DIV>"


   end

end
