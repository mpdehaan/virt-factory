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
            set_flash_on_exception(ex)
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
                @item = ManagedObject.retrieve(object_class,@session, @params[:id])
            rescue XMLRPCClientException => ex
                @item = object_class.new(@session)
                set_flash_on_exception(ex)
            end
        end
    end

    def view
        @item = ManagedObject.retrieve(object_class,session, @params[:id])
    end

    def edit_submit
        begin
            obj = ManagedObject.from_hash(object_class,@params["form"], @session)
#            print obj.methods.join("\n"), "\n"
            operation = obj.id.nil? ? "add" : "edit"
            obj.save
            @flash[:notice] = "#{object_class::METHOD_PREFIX} #{obj.objname} #{operation} succeeded."
            redirect_to :action => 'list'
            return
        rescue XMLRPCClientException => ex
            set_flash_on_exception(ex)
        end
        redirect_to :action => "edit"
    end

    def delete
        begin
            ManagedObject.delete(object_class, @params[:id] )
            @flash[:notice] = "Deleted #{object_class::METHOD_PREFIX} #{@params[:id]}"
        rescue XMLRPCClientException => ex
            set_flash_on_exception(ex)
        end
        redirect_to :action => "list"
        return
    end

    def set_flash_on_exception(ex)
        @flash[:notice] = ex.notice
        @flash[:errmsg] = ex.result["traceback"]
        @flash[:fielderrors] = ex.result["invalid-fields"]
    end

end

