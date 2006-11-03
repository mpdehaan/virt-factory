require "xmlrpc/client"

server = XMLRPC::Client.new("127.0.0.1","/",5150)

puts server.call("login","guest","guest")
puts server.call("login","guest2","guest")

