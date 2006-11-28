

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
       ATTR_LIST = { :id => {:type => Integer}, 
                     :machine_id => {:type => Integer}, 
                     :image_id => {:type => Integer}, 
                     :state => {:type => String},
                     :machine => { :type => MachineController::Machine, :id_attr => :machine_id}, 
                     :image => { :type => ImageController::Image, :id_attr => :image_id} }
       self.set_attrs(ATTR_LIST)
       print "state: ", instance_method("state"), "\n"
       METHOD_PREFIX = "deployment"

       def objname
           self.get_machine.address + ": " + self.get_image.name
       end
   end
end
