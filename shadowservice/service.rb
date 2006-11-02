require "xmlrpc/server"
require 'rubygems'
require_gem 'activerecord'

s = XMLRPC::Server.new(5150)

ActiveRecord::Base.establish_connection(
   :adapter => "sqlite3",
   :database => "/opt/shadowmanager/primary_db"
)

class User < ActiveRecord::Base
    set_table_name "users"
end

s.add_handler("login") do |user,pass| 
      item = User.find_by_username(user)
      if item.nil? or item.password != pass
          -1
      else
          item.id
      end
end

trap("INT") { s.shutdown }
s.serve
