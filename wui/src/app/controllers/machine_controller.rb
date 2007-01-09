
# the machine controller deals with management and display of physical (not virtual) hardware.

class MachineController < AbstractObjectController

   def edit
       super
       @images = []

       # when adding a new machine, the user must pick which image to use to provision that machine.
       # an image contains information about the distro + kickstart data + recipe, etc.  For bare metal,
       # we exclude appliance images that are marked as only working for virtualization. 
       # TODO:  ideally, out of the box, we'd ship and install an image that would be suitable for a stock
       # container.

       ManagedObject.retrieve_all(Image, @session).each do |image|
           @images << [image.name, image.id] unless image.valid_targets == IMAGE_IS_VIRT
       end
       @images.insert(0,EMPTY_ENTRY)
   end

   def object_class
       Machine
   end

end
