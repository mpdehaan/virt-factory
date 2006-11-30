
class MachineController < AbstractObjectController

   def edit
       super
       @distributions = ManagedObject.retrieve_all(Distribution, @session).collect do |dist|
           [dist.name, dist.id]
       end
       @distributions.insert(0,EMPTY_ENTRY)
   end

   def object_class
       Machine
   end

end
