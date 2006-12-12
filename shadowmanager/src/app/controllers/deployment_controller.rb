

class DeploymentController < AbstractObjectController

   def object_class
       Deployment
   end

   def edit
       super
       @machines = ManagedObject.retrieve_all(Machine, @session).collect do |machine|
           [machine.address, machine.id]
       end
       @machines.insert(0,EMPTY_ENTRY)
       @images = []
       ManagedObject.retrieve_all(Image, @session).each do |image|
           @images << [image.name, image.id] unless image.valid_targets == IMAGE_IS_BAREMETAL
       end
   end
end
