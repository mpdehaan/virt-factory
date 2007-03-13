
# the deployment controller controls the users view and manipulation of the deployment objects.
# deployments are associations between machines and the profiles that are installed on them.

class DeploymentController < AbstractObjectController

   def object_class
       Deployment
   end

   def edit
       super

       # get a list of address to ip mappings
       @machines = ManagedObject.retrieve_all(Machine, @session).collect do |machine|
           [machine.hostname, machine.id] unless machine.id < 0 or machine.hostname.nil?
       end
       @machines.reject! { |foo| foo.nil? }

       # start all dropdowns with a blank entry when the user first comes to them
       @machines.insert(0,EMPTY_ENTRY)

       # get a list of all profiles that are deployable.  Deployments are not used to represent
       # the mapping of the profile that is installed on a baremetal machine (the domu), deployments
       # are virtual only.

       @profiles = []
       ManagedObject.retrieve_all(Profile, @session).each do |profile|
           @profiles << [profile.name, profile.id] unless profile.id < 0 or profile.valid_targets == PROFILE_IS_BAREMETAL
       end
       @profiles.reject! { |foo| foo.nil? }

   end

    def pause
        obj = ManagedObject.retrieve(Deployment, @session, @params[:id])
        obj.pause()
        redirect_to :action=> "edit", :id => @params[:id]
    end

    def unpause
        obj = ManagedObject.retrieve(Deployment, @session, @params[:id])
        obj.unpause()
        redirect_to :action=> "edit", :id => @params[:id]
    end

    def start
        obj = ManagedObject.retrieve(Deployment, @session, @params[:id])
        obj.start()
        redirect_to :action=> "edit", :id => @params[:id]
    end

    def shutdown
        obj = ManagedObject.retrieve(Deployment, @session, @params[:id])
        obj.shutdown()
        redirect_to :action=> "edit", :id => @params[:id]
    end
    
    def destroy
        obj = ManagedObject.retrieve(Deployment, @session, @params[:id])
        obj.destroy()
        redirect_to :action=> "edit", :id => @params[:id]
    end

end

