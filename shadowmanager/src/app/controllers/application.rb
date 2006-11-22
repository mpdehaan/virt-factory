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
            @item = object_class.new
            @operation = "Add"
        else
            @item = ManagedObject.retrieve(object_class,session, @params[:id])
            @operation = "Edit"
        end
    end

    def view
        @item = ManagedObject.retrieve(object_class,session, @params[:id])
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
        
        ASSOCIATIONS = {}

        def self.retrieve_all(object_class, session)
            (rc, results) = temp_retrieve(object_class)
#hard-coding data temporarily until python api returns data
#            (rc, results) = @@server.call("#{object_class::METHOD_PREFIX}_list",session[:login])
            unless rc == ERR_SUCCESS
                raise XMLRPCClientException.new(rc, results)
            end
            results.collect {|hash| ManagedObject.from_hash(object_class,hash)}
        end

        def self.retrieve(object_class, session, id)
#            plist = { "id" => id }
#           (rc, results) = @@server.call("#{object_class::METHOD_PREFIX}_get", session[:login], plist)
#            ManagedObject.from_hash(object_class,results)
            print "ID: ", id, "\n"
            item = self.retrieve_all(object_class, session).find { |obj| obj.id.to_s == id }
            print "item: ", item, "\n"
            item
        end

        def self.temp_retrieve(object_class)
            if (object_class == UserController::User)
                [0, [ { "id" => 101,
                          "username"    => "admin",
                          "password"    => "fedora",
                          "first"       => "a",
                          "middle"      => "b",
                          "last"        => "c",
                          "description" => "d",
                          "email"       => "admin@foo.com" },
                      { "id" => 102,
                          "username"    => "guest",
                          "password"    => "guest",
                          "first"       => "e",
                          "middle"      => "f",
                          "last"        => "g",
                          "description" => "h",
                          "email"       => "guest@foo.com" }]]
             elsif (object_class == MachineController::Machine)
                [0, [ {"id" => 201, 
                          "address" => "foo.com", 
                          "architecture" => "foo_64",
                          "processor_speed" => 42,
                          "processor_count" => 4},
                      { "id" => 202, 
                          "address" => "foo2.com", 
                          "architecture" => "foo_64",
                          "processor_speed" => 42,
                          "processor_count" => 4}]]
            elsif (object_class == ImageController::Image)
                [0, [ {"id" => 301, 
                          "name" => "myimage", 
                          "version" => "55",
                          "filename" => "/tmp/foo",
                          "specname" => "foospec"},
                      { "id" => 302, 
                          "name" => "myimage2", 
                          "version" => "552",
                          "filename" => "/tmp/foo2",
                          "specname" => "foo2spec"}]]
            elsif (object_class == DeploymentController::Deployment)
                [0, [ { "id" => 401,
                          "machine_id"    => 201,
                          "image_id"    => 301,
                          "state"       => 1,
                          "machine"      => {"id" => 201, 
                              "address" => "foo.com", 
                              "architecture" => "foo_64",
                              "processor_speed" => 42,
                              "processor_count" => 4},
                          "image"      => {"id" => 301, 
                              "name" => "myimage", 
                              "version" => "55",
                              "filename" => "/tmp/foo",
                              "specname" => "foospec"} },
                      { "id" => 402,
                          "machine_id"    => 202,
                          "image_id"    => 302,
                          "state"       => 2,
                          "machine"      => {"id" => 202, 
                              "address" => "foo2.com", 
                              "architecture" => "foo_64",
                              "processor_speed" => 42,
                              "processor_count" => 4},
                          "image"      => {"id" => 302, 
                              "name" => "myimage2", 
                              "version" => "552",
                              "filename" => "/tmp/foo2",
                              "specname" => "foo2spec"} }]]
            end
        end

        def self.from_hash(object_class, hash)
            obj = object_class.new
            object_class::ATTR_LIST.each { |attr| obj.method(attr.to_s+"=").call(hash[attr.to_s]) }
            object_class::ASSOCIATIONS.each do |attr,attrinfo| 
                related_obj = self.from_hash(attrinfo[1], hash[attr.to_s])
                obj.method(attr.to_s+"=").call(related_obj) 
            end
            obj
        end
        def to_hash
            hash = Hash.new
            self.class::ATTR_LIST.each { |attr| hash[attr.to_s] = self.method(attr).call }
            self.class::ASSOCIATIONS.each do |attr,attrinfo| 
                hash[attr.to_s] = self.method(attr).call.to_hash
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
