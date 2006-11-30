

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
       @images = ManagedObject.retrieve_all(Image, @session).collect do |image|
           [image.name, image.id]
       end
   end
end
