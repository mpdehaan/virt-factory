class Image < ManagedObject
    ATTR_LIST = { :id => {:type => Integer}, 
                  :name => {:type => String}, 
                  :version => {:type => String}, 
                  :filename => {:type => String}, 
                  :specfile => {:type => String}, 
                  :distribution_id => {:type => Integer}, 
                  :distribution => { :type => Distribution, :id_attr => :distribution_id}, 
                  :virt_storage_size => {:type => Integer}, 
                  :virt_ram => {:type => Integer}, 
                  :kickstart_metadata => {:type => String},
                  :kernel_options => {:type => String},
                  :valid_targets => {:type => Integer},
                  :is_container => {:type => Integer} }
                   
    self.set_attrs(ATTR_LIST)
    METHOD_PREFIX = "image"

    def objname
        name
    end
end
