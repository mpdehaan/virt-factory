
class DistributionController < ObjectController

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
       ATTR_LIST.each {|attr,metadata| attr_accessor attr }
       METHOD_PREFIX = "distribution"

       def objname
           name
       end
   end

end
