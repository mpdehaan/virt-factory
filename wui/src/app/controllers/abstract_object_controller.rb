# the abstract object controller is the base class for all controllers that primarily
# work as CRUD interfaces on a "ManagedObject" derived model class.  

class AbstractObjectController < ApplicationController

    include ApplicationHelper

    # this is a variable that is used in making a blank entry in dropdowns for various things.  
    # FIXME: does this belong in this class?  Not sure.
    EMPTY_ENTRY = ["-None-", ""]

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
            @items = ManagedObject.retrieve_all(object_class, @session)
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
        @session[:login] = nil
        redirect_to :controller => "login", :action => "index"
    end

    # this page retrieves parameters needed to edit or add the given record.  
    # whether an edit or add is performed in the backend
    # depends on whether there was an id field attached to the submission.  adds do not
    # have an id.  either way, we retrieve an existing record (or create a new object) to
    # populate the view, and the result of either action is processed by the edit_submit
    # action.  nothing is actually done here to modify the configuration until edit_submit

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

    # view action.  What does this do?
    #---
    # FIXME: I have my suspicions that this controller method is not actually used, and rather
    # all links go to edit.  It may be the case that we want to display some things entirely
    # read only.  This may change later when we start having to worry about guest permissions,
    # but I think this can be deleted.
    #+++

    def view
        @item = ManagedObject.retrieve(object_class,session, @params[:id])
    end

    # edit submit processes all new addition calls and all edit calls.  you can tell whether
    # to call an add method or an edit method in the web service based on whether there is an
    # id in the parameter list.  There is no view associated with edit_submit, it's just
    # an action, hence the redirect to the "list" controller action on success. On failure,
    # it will stay on the same page and show an error.
    #---
    # FIXME: it would be nice for fields to not get deleted upon error, so the user
    # doesn't have to type all of them in again.
    #+++

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

    # deletes an object, redirecting to list on success, otherwise showing an error message.

    def delete
        begin
            ManagedObject.delete(object_class, @params[:id], @session)
            @flash[:notice] = "Deleted #{object_class::METHOD_PREFIX} #{@params[:id]}"
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
        # populate @flash with a human readable error string suitable by
        # display in the layout (right column callout #2)
        @flash[:errmsg] = ex.get_human_readable()
    end

end

