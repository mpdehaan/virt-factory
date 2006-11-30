
class DistributionController < AbstractObjectController

   def object_class
       Distribution
   end

   class Distribution < ManagedObject
       ATTR_LIST = { :id => {:type => Integer}, 
                     :name => {:type => String}, 
                     :kernel => {:type => String}, 
                     :initrd => {:type => String}, 
                     :options => {:type => String}, 
                     :kickstart => {:type => String} }
       self.set_attrs(ATTR_LIST)
       METHOD_PREFIX = "distribution"

       def objname
           name
       end
   end

end
