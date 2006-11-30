class Machine < ManagedObject
    ATTR_LIST = { :id => {:type => Integer}, 
                  :address => {:type => String}, 
                  :architecture => {:type => Integer}, 
                  :processor_speed => {:type => Integer}, 
                  :processor_count => {:type => Integer}, 
                  :memory => {:type => Integer},
                  :distribution_id => {:type => Integer}, 
                  :distribution => { :type => Distribution, :id_attr => :distribution_id}, 
                  :kernel_options => {:type => String}, 
                  :kickstart_metadata => {:type => String}, 
                  :list_group => {:type => String} }
    self.set_attrs(ATTR_LIST)
    METHOD_PREFIX = "machine"
end
