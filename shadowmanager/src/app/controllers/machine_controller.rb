
class MachineController < AbstractObjectController

   def edit
       super
       @images = []
       ManagedObject.retrieve_all(Image, @session).each do |image|
           @images << [image.name, image.id] unless image.valid_targets == IMAGE_IS_VIRT
       end
       @images.insert(0,EMPTY_ENTRY)
   end

   def object_class
       Machine
   end

end
