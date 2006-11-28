
class ImageController < ObjectController

   def object_class
       Image
   end

   class Image < ManagedObject
       ATTR_LIST = { :id => {:type => Integer}, 
                     :name => {:type => String}, 
                     :version => {:type => String}, 
                     :filename => {:type => String}, 
                     :specfile => {:type => String} }
       ATTR_LIST.each {|attr,metadata| attr_accessor attr }
       METHOD_PREFIX = "image"

       def objname
           name
       end
   end

end
