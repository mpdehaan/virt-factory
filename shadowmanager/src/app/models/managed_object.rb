class ManagedObject

    # marker class to identify boolean attribute types
    class Boolean
    end
    def initialize(session)
        @session = session
    end
    attr_reader :session

    def self.set_attrs(hash)
        hash.each do |attr,metadata| 
            attr_accessor attr 
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
                end
            end
        end
    end

    def save
        operation = @id.nil? ? "add" : "edit"
        ManagedObject.call_server("#{self.class::METHOD_PREFIX}_#{operation}", 
                                       @session, self.to_hash, objname)
    end

    def self.delete(object_class,id)
        self.call_server("#{object_class::METHOD_PREFIX}_delete", 
                         @session, { "id" => id }, id.to_s)
    end

    def self.retrieve_all(object_class, session)
        results = self.call_server("#{object_class::METHOD_PREFIX}_list", session, {})
        results.collect {|hash| ManagedObject.from_hash(object_class, hash, session)}
    end

    def self.retrieve(object_class, session, id)
        results = self.call_server("#{object_class::METHOD_PREFIX}_get", 
                                   session, {"id" => id }, id.to_s)
        ManagedObject.from_hash(object_class,results, session)
    end

    def self.from_hash(object_class, hash, session)
        obj = object_class.new(session)
        object_class::ATTR_LIST.each do |attr, metadata| 
            if (newval = hash[attr.to_s])
                attr_type = metadata[:type]
                if (newval.is_a?(Hash) && attr_type.methods.include?("from_hash"))
                    newval = self.from_hash(attr_type, newval, session)
                end
                unless newval.is_a?(attr_type)
                    if (attr_type == Integer)
                        if (newval.is_a?(String) && newval.empty?)
                            newval = nil
                        else
                            newval = newval.to_i 
                        end
                    elsif (attr_type == Boolean)
                        newval = [true, "true"].include?(newval) ? true : false
                    else
                        newval = attr_type.new(newval)
                    end
                end
            end
            obj.method(attr.to_s+"=").call(newval) if newval
        end
        obj
    end
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
    def objname
        id
    end

    def self.call_server(method_name, session, args, errmsg = "")
        (rc, results) = @@server.call(method_name, session[:login], args)
        unless rc == ERR_SUCCESS
            raise XMLRPCClientException.new("#{method_name} failed (#{ERRORS[rc]}): #{errmsg}", results)
        end
        results["values"]
    end
end
