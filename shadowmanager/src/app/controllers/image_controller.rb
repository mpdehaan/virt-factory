
class ImageController < ObjectController

   def object_class
       Image
   end

   class Image < ManagedObject
       ATTR_LIST = [:id, :name, :version, :filename, :specfile]
       ATTR_LIST.each {|x| attr_accessor x}
       METHOD_PREFIX = "image"

       def objname
           name
       end
   end

end
