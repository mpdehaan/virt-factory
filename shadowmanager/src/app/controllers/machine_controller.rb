
class MachineController < ObjectController

   def object_class
       Machine
   end

   class Machine < ManagedObject
       ATTR_LIST = [:id, :address, :architecture, :processors, :memory]
       ATTR_LIST.each {|x| attr_accessor x}
       METHOD_PREFIX = "machine"
   end

end
