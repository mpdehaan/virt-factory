require 'xmlrpc/client'
@@server = XMLRPC::Client.new("127.0.0.1","/",5150)


class MachineController < ApplicationController
    include ApplicationHelper

    def index
        redirect_to :action => 'list'
    end

    def list
        @items = @@server.call("get_machines")
    end

    def add
    end

    def add_submit
    end

    def delete
    end

    def delete_submit
    end

    def viewedit
    end

    def viewedit_submit
    end

end
