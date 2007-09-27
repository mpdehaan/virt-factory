
# the deployment controller controls the users view and manipulation of the deployment objects.
# deployments are associations between machines and the profiles that are installed on them.

class DeploymentController < AbstractObjectController

    def object_class
        Deployment
    end

    def edit
       
        # talk to the node daemon of the host to see what the guest's
        # current state is, and update it.
        if !params[:id].nil?
            obj = ManagedObject.retrieve(Deployment, get_login, params[:id])
            # obj.refresh() -- do not call this from WUI (at least for now)
        end

        # do the regular get stuff here.
        super

        # get a list of machines
        # do not allow a deployment to a machine if
        #  (A) the machine is the "no machine" record
        #  (B) no hostname, i.e. not completed registered yet
        #  (C) offline (i.e. no heartbeat)
        # if any of the above conditions are true, deploying to those
        # machines is not acceptible
        # FIXME: API call for get_machines_that_can_deploy (or equivalent)
        # would be useful.  TBA.
        @machines = ManagedObject.retrieve_all(Machine, get_login).collect do |machine|
            [machine.hostname, machine.id] unless machine.id < 0 or machine.hostname.nil? or machine.state == MACHINE_STATE_OFFLINE
        end
        @machines.reject! { |foo| foo.nil? }

        # start all dropdowns with a blank entry when the user first comes to them
        @machines.insert(0,EMPTY_ENTRY)

        # get a list of all profiles that are deployable.  Deployments are not used to represent
        # the mapping of the profile that is installed on a baremetal machine (the domu), deployments
        # are virtual only.

        get_valid_profiles
        #get list of current tags from virt-factory
        begin
            @tags = ManagedObject.call_server("machine_get_all_tags", get_login, {})
        rescue XMLRPCClientException => ex
            set_flash_on_exception(ex)
        end
    end

    def get_valid_profiles
       id_param = params[:machine_id]
       @profiles = []
       if !id_param.nil? and (id_param.to_i > 0)
           obj = ManagedObject.retrieve(Machine, get_login, id_param.to_i)
           @profiles = obj.get_profile_choices().collect { |x| [x["name"], x["id"]] }
           @profiles.each { |x| print "profile: ", x, "\n" }
       end
       @profiles.insert(0,EMPTY_ENTRY) if @profiles.empty?
    end

    def edit_submit
        tags = params["form"]["tags"]
        tags = [] if tags.nil?
        new_tags = params["form"]["new_tags"]
        params["form"]["tags"] = tags + new_tags.strip.split(%r{\s*,\s*})
        params["form"].delete("new_tags")
        super
    end
        
    def pause
        obj = ManagedObject.retrieve(Deployment, get_login, params[:id])
        obj.pause()
        redirect_to :action=> "edit", :id => params[:id]
    end

    def unpause
        obj = ManagedObject.retrieve(Deployment, get_login, params[:id])
        obj.unpause()
        redirect_to :action=> "edit", :id => params[:id]
    end

    def start
        obj = ManagedObject.retrieve(Deployment, get_login, params[:id])
        obj.start()
        redirect_to :action=> "edit", :id => params[:id]
    end

    def shutdown
        obj = ManagedObject.retrieve(Deployment, get_login, params[:id])
        obj.shutdown()
        redirect_to :action=> "edit", :id => params[:id]
    end
    
    def destroy
        obj = ManagedObject.retrieve(Deployment, get_login, params[:id])
        obj.destroy()
        redirect_to :action=> "edit", :id => params[:id]
    end

end

