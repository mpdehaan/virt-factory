
class ImageController < ObjectController

   def edit
       super
#       @distributions = ManagedObject.retrieve_all(DistributionController::Distribution, @session).collect do |dist|
#           [dist.name, dist.id]
#       end
       @distributions = []
   end

   def object_class
       Image
   end

   class Image < ManagedObject
       ATTR_LIST = { :id => {:type => Integer}, 
                     :name => {:type => String}, 
                     :version => {:type => String}, 
                     :filename => {:type => String}, 
                     :specfile => {:type => String}, 
                     :distribution_id => {:type => Integer}, 
                     :distribution => { :type => DistributionController::Distribution, :id_attr => :distribution_id}, 
                     :virt_storage_size => {:type => Integer}, 
                     :virt_ram => {:type => Integer}, 
                     :kickstart_metadata => {:type => String} }
       self.set_attrs(ATTR_LIST)
       METHOD_PREFIX = "image"

       def objname
           name
       end
   end

end
