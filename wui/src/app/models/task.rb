# Tasks (actually called Actions on the backend, Action is reserved by rails) represent
# background states for long running tasks.   

class Task < ManagedObject

    # corresponds with what's in the database
    ATTR_LIST = { 
        :id            => {:type => Integer },
        :user_id       => {:type => Integer }, 
        :operation     => {:type => String  }, 
        :parameters    => {:type => String  }, 
        :state         => {:type => String  }, 
        :time          => {:type => Integer }, 
        :user          => {:type => User,       :id_attr => :user_id       }
    }
                   
    self.set_attrs(ATTR_LIST)

    # web service methods start with this
    METHOD_PREFIX = "task"

    # when showing an image onscreen, just use the name field in the database
    def objname
        id
    end

end
