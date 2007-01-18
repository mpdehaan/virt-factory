# registration tokens are tokens that allow nodes to authenticate to the registration module for purpose
# of self adding the machines.  They can have a limited use count or not.  They can be associated with
# an image or not.  

class Regtoken < ManagedObject

    # corresponds with what's in the database
    ATTR_LIST = { 
        :id             => { :type => Integer }, 
        :token          => { :type => String  }, 
        :image_id       => { :type => Integer },
        :user_id        => { :type => Integer }, 
        :uses_remaining => { :type => Integer }, 
        :image          => { :type => Image, :id_attr => :image_id } 
        :user           => { :type => User, :id_attr => :user_id   }
    }
               
    self.set_attrs(ATTR_LIST)

    # web service methods start with this
    METHOD_PREFIX = "regtoken"

    def objname
        id # correct?
    end

end
