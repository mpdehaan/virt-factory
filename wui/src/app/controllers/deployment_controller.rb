
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
           [machine.hostname, machine.id]
       end

       # start all dropdowns with a blank entry when the user first comes to them
       @machines.insert(0,EMPTY_ENTRY)

       # get a list of all profiles that are deployable.  Deployments are not used to represent
       # the mapping of the profile that is installed on a baremetal machine (the domu), deployments
       # are virtual only.

       @profiles = []
       ManagedObject.retrieve_all(Profile, @session).each do |profile|
           @profiles << [profile.name, profile.id] unless profile.id < 0 or profile.valid_targets == PROFILE_IS_BAREMETAL
       end
   end
end

