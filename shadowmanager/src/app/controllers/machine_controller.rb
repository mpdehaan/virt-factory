
class MachineController < ObjectController

   def edit
       super
       @distributions = ManagedObject.retrieve_all(DistributionController::Distribution, @session).collect do |dist|
           [dist.name, dist.id]
       end
       @distributions.insert(0,EMPTY_ENTRY)
   end

   def object_class
       Machine
   end

   class Machine < ManagedObject
       ATTR_LIST = { :id => {:type => Integer}, 
                     :address => {:type => String}, 
                     :architecture => {:type => Integer}, 
                     :processor_speed => {:type => Integer}, 
                     :processor_count => {:type => Integer}, 
                     :memory => {:type => Integer},
                     :distribution_id => {:type => Integer}, 
                     :distribution => { :type => DistributionController::Distribution, :id_attr => :distribution_id}, 
                     :kernel_options => {:type => String}, 
                     :kickstart_metadata => {:type => String}, 
                     :list_group => {:type => String} }
       self.set_attrs(ATTR_LIST)
       METHOD_PREFIX = "machine"
   end

end
