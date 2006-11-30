class ManagedObject

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

    def self.retrieve_all(object_class, session)
        (rc, results) = @@server.call("#{object_class::METHOD_PREFIX}_list",session[:login])
        unless rc == ERR_SUCCESS
            raise XMLRPCClientException.new(rc, results)
        end
        results.collect {|hash| ManagedObject.from_hash(object_class,hash, session)}
    end

    def self.retrieve(object_class, session, id)
        plist = { "id" => id }
       (rc, results) = @@server.call("#{object_class::METHOD_PREFIX}_get", session[:login], plist)
        unless rc == ERR_SUCCESS
            raise XMLRPCClientException.new(rc, results)
        end
        ManagedObject.from_hash(object_class,results, session)
    end

    def self.from_hash(object_class, hash, session)
        obj = object_class.new(session)
        object_class::ATTR_LIST.each do |attr, metadata| 
            newval = hash[attr.to_s]
            if newval
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
            newval = self.method(attr).call 
            if newval
                attr_type = metadata[:type]
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
end
