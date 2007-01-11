# the managed object serves as a base class for all objects that support typical CRUD type functionality.

class ManagedObject

    # marker class to identify boolean attribute types
    # we keep track of object types for various fields when defining objects, but Ruby doesn't have a boolean type.
    # it just has things that respond to true? and so forth.  This is a workaround.
    class Boolean
    end

    # I think this means every object is constructed with a reference to the session state.  (Correct?)
    def initialize(session)
        @session = session
    end

    attr_reader :session

    # basically each subclass will have a call to set_attrs in it's constructor.  Each attr in the list
    # contains a name of a field and a type value for that field.  Each field will be made an accessor,
    # which means you can get and set that field as if it were a variable.  

    def self.set_attrs(hash)

        hash.each do |attr,metadata| 

            attr_accessor attr 

            # an object returned from the backend returns nested data containing the subobjects.  This 
            # particular code is (and I don't fully understand it -- mdehaan) there to pull in the subobjects
            # if the backend fails to include them in nested format, basically allowing the object to make 
            # extra RPC calls to fill in elements at the time they are accessed.  IMHO, it's a failure in the
            # backend if that info isn't sent over so this isn't really neccessary.  Reflection can probably
            # be limited.

            if (metadata[:id_attr])

                define_method(("get_"+attr.to_s).to_sym) do
                    if ((!instance_variable_get("@"+attr.to_s)) &&
                        (id = instance_variable_get("@"+metadata[:id_attr].to_s)) &&
                        id > 0)
                        instance_variable_set("@"+attr.to_s,
                                              ManagedObject.retrieve(metadata[:type],
                                                                     self.session,
                                                                     id))
                    end
                    instance_variable_get("@"+attr.to_s)

                end # define_method
            end # metadata[:id_attr]

        end

    end

    # the save call really maps to a foo_add or foo_edit call on the backend, based on whether
    # an id is supplied.  When editing an existing object, there is already an id, for new objects,
    # there isn't.  Basically all form fields should be passed along when editing or adding an object,
    # the backend will ignore the ones it doesn't need or can't change.

    def save
        operation = (@id.nil? ||  @id == 0) ? "add" : "edit"
        ManagedObject.call_server("#{self.class::METHOD_PREFIX}_#{operation}", 
                                       @session, self.to_hash, objname)
    end

    # deleting an object, only the id is a required argument.

    def self.delete(object_class,id,session)
        self.call_server("#{object_class::METHOD_PREFIX}_delete", 
                         session, { "id" => id }, id.to_s)
    end

    # this is a call usable in the controller to get all of the objects that the backend knows about
    #----
    # FIXME: needs to support the limit query stuff the backend knows about, so that we can do pagination
    # with really long system lists (i.e. a couple thousand).  Ok to add in later release.
    #+++

    def self.retrieve_all(object_class, session)
        results = self.call_server("#{object_class::METHOD_PREFIX}_list", session, {})
        results.collect {|hash| ManagedObject.from_hash(object_class, hash, session)}
    end

    # retrieves a single object (not a list) that corresponds to a certain id.  Should return
    # null if it isn't there, but it might raise an exception.  Need to check on this.

    def self.retrieve(object_class, session, id)
        results = self.call_server("#{object_class::METHOD_PREFIX}_get", 
                                   session, {"id" => id }, id.to_s)
        ManagedObject.from_hash(object_class,results, session)
    end


    # from_hash vivifies an object (or an object tree) using it's hash representation, recursively doing the right
    # thing as neccessary. 

    def self.from_hash(object_class, hash, session)

       # create the instance, we'll fill it's data as we go along
       object_instance = object_class.new(session)

       # for each variable passed in as input to the function
       hash.each do |key, value|
            # we're going to be creating a new object and adding it to this object as a member variable
            new_item = nil
 
            # determine the names and types of variables the instance should have
            class_attributes = object_class::ATTR_LIST[key.to_sym]
            # if we don't understand this particular variable, we have a serious problem
            raise RuntimeError.new("class attributes are unknown for #{key}") if class_attributes.nil?
             
            # how we vivify the object depends on what type it is
            atype = class_attributes[:type]
            if atype == Integer and value.is_a?(String)
                new_item = value.to_i
            elsif atype == Integer and value.is_a?(Integer)
                new_item = value
            elsif atype == Boolean
                new_item = [true,"true"].include?(value) ? true : false
            elsif atype == String
                new_item = value
            elsif atype.methods.include?("from_hash")
                # ManagedObjects result in recursive calls...
                raise RuntimeError.new("No child arguments?") if not value.is_a?(Hash) 
                new_item = self.from_hash(atype, value, session)
            else
                # we have no idea what to do with this...
                raise RuntimeError.new("Expecting ManagedObject, got #{atype.to_s}")
            end
            # this data element was processed fine, so create the item
            # this is roughly equivalent to python's setattr
            object_instance.method(key.to_s+"=").call(new_item)
            
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
    # it would be used in constructing method names, such as "image", for "image_add".

    def objname
        id
    end

    # this is a wrapper around the XMLRPC calls the various methods make.

    def self.call_server(method_name, session, args, errmsg = "")

        # the return signature for a backend API method is usually (rc, hash) where hash contains
        # one or more of the following fields.  See explanation in XMLRPCClientException class.
        (rc, rawdata) = @@server.call(method_name, session[:login], args)

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


