class Deployment < ManagedObject
    ATTR_LIST = { :id => {:type => Integer}, 
                  :machine_id => {:type => Integer}, 
                  :image_id => {:type => Integer}, 
                  :state => {:type => String},
                  :machine => { :type => Machine, :id_attr => :machine_id}, 
                  :image => { :type => Image, :id_attr => :image_id} }
    self.set_attrs(ATTR_LIST)
    print "state: ", instance_method("state"), "\n"
    METHOD_PREFIX = "deployment"

    def objname
        self.get_machine.address + ": " + self.get_image.name
    end
end
