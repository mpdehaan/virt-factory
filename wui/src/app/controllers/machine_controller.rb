
# the machine controller deals with management and display of physical (not virtual) hardware.

class MachineController < AbstractObjectController

   def edit
       super
       @profiles = []

       # when adding a new machine, the user must pick which profile to use to provision that machine.
       # an profile contains information about the distro + kickstart data + recipe, etc.  For bare metal,
       # we exclude appliance profiles that are marked as only working for virtualization. 
       # TODO:  ideally, out of the box, we'd ship and install an profile that would be suitable for a stock
       # container.

       ManagedObject.retrieve_all(Profile, @session).each do |profile|
           if !profile.nil?
               @profiles << [profile.name, profile.id] unless profile.valid_targets == PROFILE_IS_VIRT
           end
       end
       @profiles.insert(0,EMPTY_ENTRY)
   end

   def object_class
       Machine
   end

end

