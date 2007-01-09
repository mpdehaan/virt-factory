# Tasks (actually called Actions on the backend, Action is reserved by rails) represent
# background states for long running tasks.   

class Image < ManagedObject

    # corresponds with what's in the database
    ATTR_LIST = { 
        :id            => {:type => Integer }, 
        :machine_id    => {:type => Machine,    :id_attr => :machine_id    }, 
        :deployment_id => {:type => Deployment, :id_attr => :deployment_id }, 
        :user_id       => {:type => User,       :id_attr => :user_id       }, 
        :operation     => {:type => String  }, 
        :parameters    => {:type => String  }, 
        :state         => {:type => String  }, 
        :time          => {:type => Integer }, 
    }
                   
    self.set_attrs(ATTR_LIST)

    # web service methods start with this
    METHOD_PREFIX = "action"

    # when showing an image onscreen, just use the name field in the database
    def objname
        id
    end

end
