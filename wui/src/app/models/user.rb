# a user represents, mostly, a username + password and some identifying info.  Right now, access levels aren't implemented.
# any user can log in.

class User < ManagedObject
 
    # corresponds to what's in the DB schema
 
    ATTR_LIST = { :id => {:type => Integer}, 
                  :username => {:type => String}, 
                  :password => {:type => String}, 
                  :first => {:type => String}, 
                  :middle => {:type => String}, 
                  :last => {:type => String}, 
                  :description => {:type => String}, 
                  :email => {:type => String}}
    self.set_attrs(ATTR_LIST)

    # web service methods start with this

    METHOD_PREFIX = "user"

    # when showing this object in the WUI, use the username, not the first/middle/last, etc.

    def objname
        username
    end
  

end
