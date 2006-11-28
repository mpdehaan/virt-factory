require "xmlrpc/client"
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)

class XMLRPCClientException < Exception
    attr_accessor :rc, :data
    def initialize(rc, data)
        @rc = rc
        @data = data
    end    
end

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
            @flash[:notice] = "Internal Server Error"
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
        begin
            @items = ManagedObject.retrieve_all(object_class, @session)
        rescue XMLRPCClientException => ex
            @items = []
            @flash[:notice] = "Error: No #{object_class::METHOD_PREFIX}s found (#{ex.rc})."
            @flash[:errmsg] = ex.data
        end
    end

    def logout
        @session[:login] = nil
        redirect_to :controller => "login", :action => "index"
    end

    def edit
        # FIXME: error handling on "success"
        if @params[:id].nil?
            @item = object_class.new(@session)
            @operation = "Add"
        else
            begin
                @operation = "Edit"
                @item = ManagedObject.retrieve(object_class,session, @params[:id])
            rescue XMLRPCClientException => ex
                @item = object_class.new(@session)
                @flash[:notice] = "Error:  #{object_class::METHOD_PREFIX} with ID #{@params[:id]} not found (#{ex.rc})."
                @flash[:errmsg] = ex.data
            end
        end
    end

    def view
        @item = ManagedObject.retrieve(object_class,session, @params[:id])
    end

    def edit_submit
        obj = ManagedObject.from_hash(object_class,@params["form"], @session)
        id = obj.id
        if id.nil?
            operation = "add"
        else
            operation = "edit"
        end
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

        def initialize(session)
            @session = session
        end
        attr_reader :session

        def self.set_attrs(hash)
            hash.each do |attr,metadata| 
                attr_accessor attr 
                if (metadata[:id_attr])
                    define_method(("get_"+attr.to_s).to_sym) do
                        if ((!instance_variable_get("@"+attr.to_s)) &&
                            (id = instance_variable_get("@"+metadata[:id_attr].to_s)))
                            instance_variable_set("@"+attr.to_s,
                                                  ManagedObject.retrieve(metadata[:type],
                                                                         self.session,
                                                                         id))
                        end
                        instance_variable_get("@"+attr.to_s)
                    end
                end
            end
        end

        def self.retrieve_all(object_class, session)
            (rc, results) = @@server.call("#{object_class::METHOD_PREFIX}_list",session[:login])
            unless rc == ERR_SUCCESS
                raise XMLRPCClientException.new(rc, results)
            end
            results.collect {|hash| ManagedObject.from_hash(object_class,hash, session)}
        end

        def self.retrieve(object_class, session, id)
            plist = { "id" => id }
           (rc, results) = @@server.call("#{object_class::METHOD_PREFIX}_get", session[:login], plist)
            unless rc == ERR_SUCCESS
                raise XMLRPCClientException.new(rc, results)
            end
            ManagedObject.from_hash(object_class,results, session)
        end

        def self.from_hash(object_class, hash, session)
            obj = object_class.new(session)
            object_class::ATTR_LIST.each do |attr, metadata| 
                newval = hash[attr.to_s]
                if newval
                    attr_type = metadata[:type]
                    if (newval.is_a?(Hash) && attr_type.methods.include?("from_hash"))
                        newval = self.from_hash(attr_type, newval, session)
                    end
                    unless newval.is_a?(attr_type)
                        if (attr_type == Integer)
                            if (newval.is_a?(String) && newval.empty?)
                                newval = nil
                            else
                                newval = newval.to_i 
                            end
                        else
                            newval = attr_type.new(newval)
                        end
                    end
                end
                obj.method(attr.to_s+"=").call(newval) if newval
            end
             obj
        end
        def to_hash
            hash = Hash.new
            self.class::ATTR_LIST.each do |attr, metadata|
                newval = self.method(attr).call 
                if newval
                    attr_type = metadata[:type]
                    if (newval.methods.include?("to_hash"))
                        newval = newval.to_hash
                    end
                    hash[attr.to_s] = newval 
                end
            end
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
