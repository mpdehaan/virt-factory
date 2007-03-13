# the deployment is the mapping between an profile definition (profile) and a machine that can run virtual profiles.
# deployments are only used for virtual installs (i.e. DomU's).  

class Deployment < ManagedObject

    # corresponds to what's in the database schema
    ATTR_LIST = { 
       :id                 => { :type => Integer }, 
       :hostname           => { :type => String  },
       :ip_address         => { :type => String  },
       :registration_token => { :type => String }, 
       :mac_address        => { :type => String  },
       :machine_id         => { :type => Integer }, 
       :profile_id         => { :type => Integer }, 
       :state              => { :type => String  },
       :display_name       => { :type => String  }, 
       :puppet_node_diff   => { :type => String  },
       :machine            => { :type => Machine, :id_attr => :machine_id }, 
       :profile            => { :type => Profile, :id_attr => :profile_id },
       :netboot_enabled    => { :type => Integer },
       :is_locked          => { :type => Integer } 
    }
    self.set_attrs(ATTR_LIST)
     
    # FIXME: state will eventually need to be a drop down or be controlled by a button that causes other actions
    # it may already be an integer in the datamodel, actually. sqlite doesn't enforce it.  need to check.

    METHOD_PREFIX = "deployment"

    # FIXME: is this the name used for display purposes in the GUI?
    
    def objname()
        self.get_machine().hostname + ": " + self.get_profile().name
    end

    def __virt_call(id, op)
        ManagedObject.call_server(op, @session, { "id" => id }, id.to_s)
    end

    def pause
        __virt_call(self.id, "deployment_pause")
    end

    def unpause
        __virt_call(self.id, "deployment_unpause")
    end

    def destroy
        __virt_call(self.id, "deployment_shutdown")
    end

    def start
        __virt_call(self.id, "deployment_start")
    end

    def shutdown
        __virt_call(self.id, "deployment_shutdown")
    end

end

