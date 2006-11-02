require "xmlrpc/server"

s = XMLRPC::Server.new(5150)

class LoginHandler
   def login(user, pass)
      # FIXME: activerecord
      return { "success" => True, "id" =>12345 }
   end
end

# FIXME: this *used* to be a security hole, research this...
s.add_handler("login", LoginHandler.new())

s.serve
