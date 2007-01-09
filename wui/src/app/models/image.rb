# images are system profiles + distribution information, both virtual and not.  Some are appliances, others are specifications
# for machines that will contain one or more appliances

class Image < ManagedObject

    # corresponds with what's in the database
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

    # web service methods start with this
    METHOD_PREFIX = "image"

    # when showing an image onscreen, just use the name field in the database
    def objname
        name
    end

end
