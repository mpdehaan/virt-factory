class AbstractObjectController < ApplicationController
    include ApplicationHelper
    EMPTY_ENTRY = ["-None-", ""]

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

end

