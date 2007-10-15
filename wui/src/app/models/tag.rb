# a tag is a string that is applied to a machine or deployment

class Tag < ManagedObject
 
    # corresponds to what's in the DB schema
 
    ATTR_LIST = { 
        :id             => {:type => String}, 
        :name           => {:type => String}, 
        :machines       => {:type => [Array, Machine], :id_attr => :machine_ids},
        :machine_ids    => {:type => [Array, Integer]},
        :deployments    => {:type => [Array, Deployment], :id_attr => :deployment_ids},
        :deployment_ids => {:type => [Array, Integer]}
    }
    self.set_attrs(ATTR_LIST)

    # web service methods start with this

    METHOD_PREFIX = "tag"

    # when showing this object in the WUI, use the username, not the first/middle/last, etc.

    def objname
        name
    end
  
end
