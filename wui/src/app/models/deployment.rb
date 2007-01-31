# the deployment is the mapping between an image definition (image) and a machine that can run virtual images.
# deployments are only used for virtual installs (i.e. DomU's).  

class Deployment < ManagedObject

    # corresponds to what's in the database schema
    ATTR_LIST = { 
       :id               => { :type => Integer }, 
       :hostname         => { :type => String  },
       :ip_address       => { :type => String  },
       :mac_address      => { :type => String  },
       :machine_id       => { :type => Integer }, 
       :image_id         => { :type => Integer }, 
       :state            => { :type => String  },
       :display_name     => { :type => String  }, 
       :puppet_node_diff => { :type => String  },
       :machine          => { :type => Machine, :id_attr => :machine_id }, 
       :image            => { :type => Image, :id_attr => :image_id} 
    }
    self.set_attrs(ATTR_LIST)
     
    # FIXME: state will eventually need to be a drop down or be controlled by a button that causes other actions
    # it may already be an integer in the datamodel, actually. sqlite doesn't enforce it.  need to check.

    METHOD_PREFIX = "deployment"

    # FIXME: is this the name used for display purposes in the GUI?
    
    def objname()
        self.get_machine().address + ": " + self.get_image().name
    end

end
