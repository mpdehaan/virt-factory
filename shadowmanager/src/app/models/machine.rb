
class Machine < ManagedObject
    ATTR_LIST = { :id => {:type => Integer}, 
                  :address => {:type => String}, 
                  :architecture => {:type => Integer}, 
                  :processor_speed => {:type => Integer}, 
                  :processor_count => {:type => Integer}, 
                  :memory => {:type => Integer},
                  :image_id => {:type => Integer}, 
                  :image => { :type => Image, :id_attr => :image_id},
                  :kernel_options => {:type => String}, 
                  :kickstart_metadata => {:type => String}, 
                  :list_group => {:type => String}, 
                  :mac_address => {:type => String}, 
                  :is_container => {:type => Integer} }
    self.set_attrs(ATTR_LIST)
    METHOD_PREFIX = "machine"

    def save
        self.is_container = self.image.is_container if self.get_image
        super
    end
end
