# the managed object serves as a base class for all objects that support typical CRUD type functionality.

class ManagedObject

    # marker class to identify boolean attribute types
    # we keep track of object types for various fields when defining objects, but Ruby doesn't have a boolean type.
    # it just has things that respond to true? and so forth.  This is a workaround.
    class Boolean
    end

    # each object is created with a reference to the login token for
    # connecting to the xmlrpc server.
    def initialize(login)
        @login = login
    end

    attr_reader :login

    # basically each subclass will have a call to set_attrs in it's constructor.  Each attr in the list
    # contains a name of a field and a type value for that field.  Each field will be made an accessor,
    # which means you can get and set that field as if it were a variable.  

    def self.set_attrs(hash)

        # hash is the parameter passed in by the contructor, it looks like...
        #     { :field_name => { :type => FooClass }, ... } where FooClass is Integer, String, Boolean, or 
        #     a subclass of Managed Object.
  
        hash.each do |attr,metadata| 

            attr_accessor attr 

            # an object returned from the backend returns nested data containing the subobjects.  This bit of
            # the function creates a method called get_foo for every foo that is a subobject, that will, if needed,
            # retrieve it in the event the item wasn't in the XML.

            # in general, this could cause problems if a list call fails to nest information as it would
            # generate a gazillion XMLRPC calls, causing lots of UI slowdown.  For this reason, avoid calling 
            # get_foo inside of list controller methods.

            if (metadata[:id_attr])

                method_symbol = ("get_"+ attr.to_s).to_sym    # name of method to create
                attr_symbol   = "@"+attr.to_s                 # object attribute
                id_symbol     = "@"+metadata[:id_attr].to_s   # integer id of object

                define_method(method_symbol) do

                    # if we haven't yet defined the subobject (by pulling it out of the hash)
                    # get it from the web service, otherwise return it directly
                   
                    if !instance_variable_get(attr_symbol)
                        id = instance_variable_get(id_symbol) 
                        if (id >= 0)
                           object = ManagedObject.retrieve(metadata[:type], self.login, id) 
                           instance_variable_set(attr_symbol, object)
                        end
                    end
                    return instance_variable_get(attr_symbol)

                end # define_method

            end # metadata[:id_attr]

        end

    end

    # the save call really maps to a foo_add or foo_edit call on the backend, based on whether
    # an id is supplied.  When editing an existing object, there is already an id, for new objects,
    # there isn't.  Basically all form fields should be passed along when editing or adding an object,
    # the backend will ignore the ones it doesn't need or can't change.

    def save
        operation = (@id.nil? ||  @id < 0) ? "add" : "edit"
        ManagedObject.call_server("#{self.class::METHOD_PREFIX}_#{operation}", 
                                       self.login, self.to_hash, objname)
    end

    # deleting an object, only the id is a required argument.

    def self.delete(object_class,id,login)
        self.call_server("#{object_class::METHOD_PREFIX}_delete", 
                         login, { "id" => id }, id.to_s)
    end

    # this is a call usable in the controller to get all of the objects that the backend knows about
    #----
    # FIXME: needs to support the limit query stuff the backend knows about, so that we can do pagination
    # with really long system lists (i.e. a couple thousand).  Ok to add in later release.
    #+++

    def self.retrieve_all(object_class, login, retrieve_nulls = false)
        #print "calling retrieve all for: #{object_class::METHOD_PREFIX}_list\n"
        results = self.call_server("#{object_class::METHOD_PREFIX}_list", login, {})
        results = results.collect {|hash| ManagedObject.from_hash(object_class, hash, login) if !hash.nil? and (retrieve_nulls or hash["id"] >= 0) }
        results.reject! { |foo| foo.nil? }
        return results
    end

    # retrieves a single object (not a list) that corresponds to a certain id.  Should return
    # null if it isn't there, but it might raise an exception.  Need to check on this.

    def self.retrieve(object_class, login, id)
        results = self.call_server("#{object_class::METHOD_PREFIX}_get", 
                                   login, {"id" => id }, id.to_s)
        ManagedObject.from_hash(object_class,results, login)
    end

    #updates an existing instance with attributes form a passed-in hash

    def update_from_hash(hash, login)
        ManagedObject.from_hash(self.class, hash, login, self)
    end

    # from_hash vivifies an object (or an object tree) using it's hash representation, recursively doing the right
    # thing as neccessary. 

    def self.from_hash(object_class, hash, login, object_instance = nil)

       # create the instance, we'll fill it's data as we go along
       object_instance = object_class.new(login) if object_instance.nil?

       # initially create nil values for everything, even if not in passed-in arguments.
       object_class::ATTR_LIST.each do |sym,meta|
           object_instance.method(sym.to_s+"=").call(nil)
       end

       # for each variable passed in as input to the function
       if !hash.nil? 
            hash.each do |key, value|
                # we're going to be creating a new object and adding it to this object as a member variable
               new_item = nil
 
                # determine the names and types of variables the instance should have
               class_attributes = object_class::ATTR_LIST[key.to_sym]
               # if we don't understand this particular variable, we have a serious problem
               raise RuntimeError.new("class attributes are unknown for #{key}") if class_attributes.nil?
             
               # how we vivify the object depends on what type it is
               atype = class_attributes[:type]
               if [ Fixnum, Integer ].include?(atype) and value.kind_of?(String)
                   new_item = value.empty? ? nil : value.to_i()
               elsif [ Float ].include?(atype) and value.kind_of?(String)
                   new_item = value.empty? ? nil : value.to_f()
               elsif [ Fixnum, Integer, Float ].include?(atype) and value.kind_of?(Numeric)
                   new_item = value
               elsif atype == Boolean
                   new_item = [true,"true"].include?(value) ? true : false
               elsif atype == String
                   new_item = value
               elsif atype.methods.include?("from_hash")
                   # ManagedObjects result in recursive calls...
                   raise RuntimeError.new("No child arguments?") if not value.is_a?(Hash) 
                   new_item = self.from_hash(atype, value, login)
               else
                   # we have no idea what to do with this...
                   raise RuntimeError.new("Model class #{object_class.to_s} load error for #{key} of type #{atype.to_s} and value type #{value.class()}")
               end
               # this data element was processed fine, so create the item
               # this is roughly equivalent to python's setattr
               object_instance.method(key.to_s+"=").call(new_item)
          end            

       end

       # no execeptions, so it's safe to return the constructed object.
       return object_instance

    end

    

    # this function is called when needing to map an object back into something that is usable as XMLRPC
    # arguments, for instance, when editing a form and needing to send down the new values.

    def to_hash
        hash = Hash.new
        self.class::ATTR_LIST.each do |attr, metadata|
            if (newval = self.method(attr).call)
                if (newval.methods.include?("to_hash"))
                    newval = newval.to_hash
                end
                hash[attr.to_s] = newval 
            end
        end
        hash
    end

    # FIXME: what is id in this case?  is it a global?  a string?  it seems like this should return a string.
    # Anyhow, this is the base class, and in other classes we see this being the name of the managed object as
    # it would be used in constructing method names, such as "profile", for "profile_add".

    def objname
        id
    end

    # this is a wrapper around the XMLRPC calls the various methods make.

    def self.call_server(method_name, login, args, errmsg = "")

        # the return signature for a backend API method is usually (rc, hash) where hash contains
        # one or more of the following fields.  See explanation in XMLRPCClientException class.
 
        (rc, rawdata) = @@server.call(method_name, login, args)

        unless rc == ERR_SUCCESS
            # convert error codes to Ruby exceptions.  We don't use XMLRPC faults because it's harder
            # to add extra useful data into the fault, and often with the backend data model, we have
            # additional information to pass on with errors, such as invalid field names and reasons,
            # for instance.
            raise XMLRPCClientException.new(rc, rawdata)
        end

        # the call succeeded, so go ahead and return the data object.
        # TODO: in some cases, the job_id field will prove important
        # though what the WUI needs to do with it would be TBA.  AJAXy
        # job_id tracking by keeping a list in @session would rock.

        return rawdata["data"]
    end
end



