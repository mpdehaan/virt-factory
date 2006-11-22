

class DeploymentController < ObjectController

   def object_class
       Deployment
   end

   def edit
       super
       @machines = ManagedObject.retrieve_all(MachineController::Machine, @session).collect do |machine|
           [machine.address, machine.id]
       end
       @images = ManagedObject.retrieve_all(ImageController::Image, @session).collect do |image|
           [image.name, image.id]
       end
   end

   class Deployment < ManagedObject
       ATTR_LIST = [:id, :machine_id, :image_id, :state]
       ASSOCIATIONS = {:machine => [:machine_id, MachineController::Machine], :image => [:image_id, ImageController::Image]}
       ATTR_LIST.each {|x| attr_accessor x}
       ASSOCIATIONS.each {|x,y| attr_accessor x}
       METHOD_PREFIX = "deployment"

       def objname
           username
       end
   end
end
