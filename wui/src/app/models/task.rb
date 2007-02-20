# Tasks (actually called Actions on the backend, Action is reserved by rails) represent
# background states for long running tasks.   

class Task < ManagedObject

    # corresponds with what's in the database
    ATTR_LIST = { 
        :id            => { :type => Integer },
        :user_id       => { :type => Integer },
        :user          => { :type => User,       :id_attr => :user_id },
        :machine_id    => { :type => Integer },  
        :machine       => { :type => Machine ,   :id_attr => :machine_id },
        :deployment_id => { :type => Integer }, 
        :deployment    => { :type => Deployment, :id_attr => :deployment_id },
        :action_type   => { :type => String },
        :time          => { :type => Integer }, 
    }
                   
    self.set_attrs(ATTR_LIST)

    # web service methods start with this
    METHOD_PREFIX = "task"

    # when showing a profile onscreen, just use the name field in the database
    def objname
        id
    end

end
