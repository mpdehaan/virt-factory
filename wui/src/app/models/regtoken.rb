# registration tokens are tokens that allow nodes to authenticate to the registration module for purpose
# of self adding the machines.  They can have a limited use count or not.  They can be associated with
# an profile or not.  

class Regtoken < ManagedObject

    # corresponds with what's in the database
    ATTR_LIST = { 
        :id             => { :type => Integer }, 
        :token          => { :type => String  }, 
        :profile_id     => { :type => Integer },
        :uses_remaining => { :type => Integer }, 
        :profile        => { :type => Profile, :id_attr => :profile_id } 
    }
               
    self.set_attrs(ATTR_LIST)

    # web service methods start with this
    METHOD_PREFIX = "regtoken"

    def objname
        id # correct?
    end

end
