
# the deployment controller controls the users view and manipulation of the deployment objects.
# deployments are associations between machines and the images that are installed on them.

class DeploymentController < AbstractObjectController

   def object_class
       Deployment
   end

   def edit
       super

       # get a list of address to ip mappings
       @machines = ManagedObject.retrieve_all(Machine, @session).collect do |machine|
           [machine.address, machine.id]
       end

       # start all dropdowns with a blank entry when the user first comes to them
       @machines.insert(0,EMPTY_ENTRY)

       # get a list of all images that are deployable.  Deployments are not used to represent
       # the mapping of the image that is installed on a baremetal machine (the domu), deployments
       # are virtual only.

       @images = []
       ManagedObject.retrieve_all(Image, @session).each do |image|
           @images << [image.name, image.id] unless image.valid_targets == IMAGE_IS_BAREMETAL
       end
   end
end
