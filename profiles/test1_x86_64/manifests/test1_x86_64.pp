# hello-world.pp

class helloworld1 {
    file { "/tmp/hello-world1":
        source => "puppet://$server/applianceexample/hello-world1"
    }
}

class helloworld2 {
    file { "/tmp/hello-world2":
        source => "puppet://$server/applianceexample/hello-world2"
    }
}
