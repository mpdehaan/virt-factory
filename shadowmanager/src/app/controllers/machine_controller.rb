
class MachineController < AbstractObjectController

   def edit
       super
       @images = ManagedObject.retrieve_all(Image, @session).collect do |image|
           [image.name, image.id]
       end
       @images.insert(0,EMPTY_ENTRY)
   end

   def object_class
       Machine
   end

end
