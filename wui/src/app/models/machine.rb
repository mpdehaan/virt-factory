# a machine is a piece of hardware, it won't be virtual.  It runs exactly one profile, which may either be a baremetal appliance
# or an appliance container (in which case, the profile represents a dom0 + special sauce).  

# deployments, another model object, are the association between machines (but only machines that are appliance containers and
# not pure appliances) and the profiles that run on them.

class Machine < ManagedObject

    # corresponds with db schema
    ATTR_LIST = { :id => {:type => Integer}, 
                  :hostname => {:type => String}, 
                  :registration_token => {:type => String},
                  :ip_address => {:type => String},
                  :architecture => {:type => String}, 
                  :processor_speed => {:type => Integer}, 
                  :processor_count => {:type => Integer}, 
                  :memory => {:type => Integer},
                  :profile_id => {:type => Integer}, 
                  :profile => { :type => Profile, :id_attr => :profile_id},
                  :kernel_options => {:type => String}, 
                  :kickstart_metadata => {:type => String}, 
                  :list_group => {:type => String}, 
                  :mac_address => {:type => String}, 
                  :is_container => {:type => Integer}, 
                  :netboot_enabled => { :type => Integer },
                  :puppet_node_diff => {:type => String},
                  :is_locked => {:type => Integer},
                  :last_heartbeat => {:type => Integer},
                  :state => {:type => String},
                  :tags => {:type => [Array, Tag]},
                  :tag_ids => {:type => [Array, Integer]}#,
#                  :new_tags => {:type => String}
    }

    self.set_attrs(ATTR_LIST)

    # WebSvc methods start with this
    METHOD_PREFIX = "machine"

    # I think this means that the GUI objects using this class won't set the is_container field, and we set
    # that field based on whether or not the profile field was null or not.  Though since I think the get_profile
    # methods are based on the reflectiony stuff, this may cause an RPC call.  Is that needed?  Anyhow, 
    # fill in explanation here.

    def save
        self.is_container = self.profile.is_container unless self.profile.nil?
        super
    end

    def label
        "#{self.hostname} (#{self.mac_address})"
    end
    def id_str
        "#{self.id}"
    end

    def get_profile_choices
        ManagedObject.call_server("machine_get_profile_choices", 
                                  self.login, { "id" => id }, id.to_s)
    end

end

