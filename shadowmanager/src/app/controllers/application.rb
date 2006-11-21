require "xmlrpc/client"
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class ApplicationController < ActionController::Base

   before_filter :login_required
   layout "shadowmanager-layout"

   def login_required
      unless @session[:login]
         redirect_to :controller => "login", :action => "input"
         return false
      end
      begin
         (rc, data) = @@server.call("token_check", @session[:login])
      rescue RuntimeError
         # internal server error (500) likely here if connection to web svc was
         # severed by a restart of the web service during development.
         redirect_to :controller => "login", :action => "input"
         return false 
      end
      unless rc == ERR_SUCCESS
         # token has timed out, so redirect here and get a new one
         # rather than having to do a lot of duplicate error handling in other places
         @flash[:notice] = "Session timeout (#{rc.class})."
         redirect_to :controller => "login", :action => "input"
         return false
      end
   end

end

# FIXME do something with the return data upon error (could be an error message or traceback
class ObjectController < ApplicationController
   include ApplicationHelper

   def index
       redirect_to :action => 'list'
   end

   def list
       (rc, results) = @@server.call("#{object_class::METHOD_PREFIX}_list",@session[:login])
       unless rc == ERR_SUCCESS
           @items = []
           @flash[:notice] = "Error: No #{object_class::METHOD_PREFIX}s found (#{rc})."
           @flash[:errmsg] = results
       else
           @items = results.collect {|hash| ManagedObject.from_hash(object_class,hash)}
       end
   end

   def logout
       @session[:login] = nil
       redirect_to :controller => "login", :action => "index"
   end

   def edit
       # FIXME: error handling on "success"
       if @params[:id].nil?
           @item = object_class.new
           @operation = "Add"
       else
           plist = { "id" => @params[:id] }
           (rc, item_hash) = @@server.call("#{object_class::METHOD_PREFIX}_get", @session[:login], plist)
           @item = ManagedObject.from_hash(object_class,item_hash)
           @operation = "Edit"
       end
   end

   def edit_submit
       obj = ManagedObject.from_hash(object_class,@params["form"])
       id = obj.id
       if id.nil? || id.empty?
           operation = "add"
       else
           operation = "edit"
       end
       print "#{object_class::METHOD_PREFIX}_#{operation}, #{obj.to_hash}\n"
       (rc, data) = @@server.call("#{object_class::METHOD_PREFIX}_#{operation}", @session[:login], obj.to_hash)
       unless rc == ERR_SUCCESS
           @flash[:notice] = "#{object_class::METHOD_PREFIX} #{operation} failed (#{rc})."
           @flash[:errmsg] = data
          redirect_to :action => "edit"
          return
      else
           @flash[:notice] = "#{object_class::METHOD_PREFIX} #{obj.objname} #{operation} succeeded."
           redirect_to :action => 'list'
           return
       end
   end

   def delete
           plist = { "id" => @params[:id] }
       (rc, data) = @@server.call("#{object_class::METHOD_PREFIX}_delete", @session[:login], plist)
       @flash[:notice] = "Deleted #{object_class::METHOD_PREFIX} #{@params[:id]}"
       unless rc == ERR_SUCCESS
          @flash[:notice] = "#{object_class::METHOD_PREFIX} #{@params[:id]} deletion failed (#{rc})"
          @flash[:errmsg] = data
       else
          @flash[:notice] = "#{object_class::METHOD_PREFIX} #{@params[:id]} deleted."
       end
       redirect_to :action => "list"
       return
   end

   def viewedit
   end

   def viewedit_submit
   end

   class ManagedObject

       def self.from_hash(object_class, hash)
           obj = object_class.new
           object_class::ATTR_LIST.each { |attr| obj.method(attr.to_s+"=").call(hash[attr.to_s]) }
           obj
       end
       def to_hash
           hash = Hash.new
           self.class::ATTR_LIST.each { |attr| hash[attr.to_s] = self.method(attr).call }
           hash
       end
       def objname
           id
       end
   end
end

class ApplicationControllerUnlocked < ActionController::Base
   layout "shadowmanager-layout"

end


