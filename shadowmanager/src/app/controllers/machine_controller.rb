
class MachineController < ObjectController

   def object_class
       Machine
   end

   class Machine < ManagedObject
       ATTR_LIST = { :id => {:type => Integer}, 
                     :address => {:type => String}, 
                     :architecture => {:type => Integer}, 
                     :processor_speed => {:type => Integer}, 
                     :processor_count => {:type => Integer}, 
                     :memory => {:type => Integer} }
       ATTR_LIST.each {|attr,metadata| attr_accessor attr }
       METHOD_PREFIX = "machine"
   end

end
