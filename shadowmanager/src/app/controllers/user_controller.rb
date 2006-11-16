

class UserController < ObjectController

   def object_class
       User
   end

   class User < ManagedObject
       ATTR_LIST = [:id, :username, :password, :first, :middle, :last, :description, :email]
       ATTR_LIST.each {|x| attr_accessor x}
       METHOD_PREFIX = "user"

       def objname
           username
       end
   end
end
