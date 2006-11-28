

class UserController < ObjectController

   def object_class
       User
   end

   class User < ManagedObject
       ATTR_LIST = { :id => {:type => Integer}, 
                     :username => {:type => String}, 
                     :password => {:type => String}, 
                     :first => {:type => String}, 
                     :middle => {:type => String}, 
                     :last => {:type => String}, 
                     :description => {:type => String}, 
                     :email => {:type => String}}
       self.set_attrs(ATTR_LIST)
       METHOD_PREFIX = "user"

       def objname
           username
       end
   end
end
