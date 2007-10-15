
# the machine controller deals with management and display of physical (not virtual) hardware.

class MachineController < AbstractObjectController

    def edit

        # talk to the node daemon of the host to see what the guest's
        # current state is, and update it.
        if !params[:id].nil?
            obj = ManagedObject.retrieve(Machine, get_login, params[:id])
            # obj.refresh() -- do not call this from WUI (at least for now)
            @profile_choices = obj.get_profile_choices().collect { |x| x["name"] }
            results = ManagedObject.call_server("task_get_by_machine", get_login, 
                                               {"machine_id"=> params[:id]})
            @tasks = results.collect {|hash| ManagedObject.from_hash(Task, hash, get_login) }
        end


        super
        @profiles = []

        # when adding a new machine, the user must pick which profile to use to provision that machine.
        # an profile contains information about the distro + kickstart data + recipe, etc.  For bare metal,
        # we exclude appliance profiles that are marked as only working for virtualization. 
        # TODO:  ideally, out of the box, we'd ship and install an profile that would be suitable for a stock
        # container.

        ManagedObject.retrieve_all(Profile, get_login, true).each do |profile|
            if !profile.nil?
                @profiles << [profile.name, profile.id] unless profile.valid_targets == PROFILE_IS_VIRT
            end
        end

        #get list of current tags from virt-factory
        begin
            @tags = ManagedObject.call_server("tag_get_names", get_login, {})
        rescue XMLRPCClientException => ex
            set_flash_on_exception(ex)
        end
    end

    def edit_submit
        tags = params["form"]["tags"]
        tags = [] if tags.nil?
        new_tags = params["form"]["new_tags"]
        params["form"]["tags"] = tags + new_tags.strip.split(%r{\s*,\s*})
        params["form"].delete("new_tags")
        super
    end
        
    def object_class
        Machine
    end

end

