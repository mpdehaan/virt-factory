# a distribution is imported via "service.py import" and is not tweaked through the GUI, but is possibly viewable.

class Distribution < ManagedObject

    # corresponds to fields in the database
    ATTR_LIST = { :id => {:type => Integer}, 
                  :name => {:type => String}, 
                  :kernel => {:type => String}, 
                  :initrd => {:type => String}, 
                  :options => {:type => String}, 
                  :kickstart => {:type => String},
                  :architecture => {:type => Integer}, 
                  :kernel_options => {:type => String}, 
                  :kickstart_metadata => {:type => String} }

    self.set_attrs(ATTR_LIST)

    # CRUD-like methods start with string
    METHOD_PREFIX = "distribution"

    # when displaying the name, just show it as it's in the DB.
    def objname
        name
    end

end
