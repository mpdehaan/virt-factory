# the abstract object controller is the base class for all controllers that primarily
# work as CRUD interfaces on a "ManagedObject" derived model class.  

class AbstractObjectController < ApplicationController

    include ApplicationHelper

    # this is a variable that is used in making a blank entry in dropdowns for various things.  
    # FIXME: does this belong in this class?  Not sure.
    EMPTY_ENTRY = ["-None-", ""]
    EMPTY_ENTRY_NOT_NONE = [ "~None~", "-1"]

    # by default, requesting a URL of the form /controller instead of /controller/action will
    # always redirect to the list page for controller.
    
    def index
        redirect_to :action => 'list'
    end

    # the list page lists all objects in the controller.
    #---
    # FIXME: needs to support pagination and limit queries.  
    # limit queries are already supported in the backend.
    #+++
    # along with each item listed there should be a link to delete the item
    # or edit it, which corresponds to the edit and delete actions respectively.

    def list
        begin
            @items = ManagedObject.retrieve_all(object_class, get_login)
        rescue XMLRPCClientException => ex
            @items = []
            set_flash_on_exception(ex)
        end
    end

    # logs the user out.  While this is valid on every object, it is only included in
    # the view for the user controller. 
    #---
    # FIXME: should be moved to the user controller.
    #+++

    def logout
        session[:login] = nil
        redirect_to :controller => "login", :action => "index"
    end

    def get_login
        session[:login]
    end
    # this page retrieves parameters needed to edit or add the given record.  
    # whether an edit or add is performed in the backend
    # depends on whether there was an id field attached to the submission.  adds do not
    # have an id.  either way, we retrieve an existing record (or create a new object) to
    # populate the view, and the result of either action is processed by the edit_submit
    # action.  nothing is actually done here to modify the configuration until edit_submit

    def edit

        if params[:id].nil?
            @item = object_class.new(get_login)
            @operation = "add"
        else
            begin
                @operation = "edit"
                @item = ManagedObject.retrieve(object_class,get_login, params[:id])
            rescue XMLRPCClientException => ex
                @item = object_class.new(get_login)
                set_flash_on_exception(ex)
            end
        end
        if params[:item_from_flash] == "1"
           @item.update_from_hash(flash[:err_item_hash], get_login)
        end
    end

    # view action.  Just shows items without an edit controls.  The individual view pages
    # should link to the edit controller for each item.

    def view
        @item = ManagedObject.retrieve(object_class,get_login, params[:id])
    end

    # edit submit processes all new addition calls and all edit calls.  you can tell whether
    # to call an add method or an edit method in the web service based on whether there is an
    # id in the parameter list.  There is no view associated with edit_submit, it's just
    # an action, hence the redirect to the "list" controller action on success. On failure,
    # it will stay on the same page and show an error.

    def edit_submit
        begin
            obj = ManagedObject.from_hash(object_class,params["form"], get_login)
            operation = obj.id.nil? ? "add" : "edit"
            obj.save()
            flash[:notice] = _("#{object_class::METHOD_PREFIX} #{obj.objname} #{operation} succeeded.")
            redirect_to :action => 'list'
            return
        rescue XMLRPCClientException => ex
            set_flash_on_exception(ex)
            flash[:err_item_hash] = params["form"]
        end
        # what page we redirect depends on whether this was an add or an edit
        if operation == "add"
            redirect_to :action => "edit", :item_from_flash => 1
        else 
            redirect_to :action => "edit", :item_from_flash => 1, :id => obj.id
        end
    end

    # deletes an object, redirecting to list on success, otherwise showing an error message.

    def delete
        begin
            ManagedObject.delete(object_class, params[:id], get_login)
            flash[:notice] = _("Deleted #{object_class::METHOD_PREFIX} #{params[:id]}")
        rescue XMLRPCClientException => ex
            set_flash_on_exception(ex)
        end
        redirect_to :action => "list"
        return
    end

    private
    
    # this is not an action, but rather a helper function.  When an exception is
    # encountered this populates the temporary flash variable with the contents of
    # the exception, as determined by the exception.  That is, the exceptions should know
    # how to explain themselves in friendly user-speak and we can ask them to do that.
    
    def set_flash_on_exception(ex)
        # populate flash with a human readable error string suitable by
        # display in the WUI
        flash[:errmsg] = ex.get_human_readable()

        flash[:invalid_fields] = ex.invalid_fields
    end

end

