# hello-world.pp

class helloworld1 {
    file { "/tmp/hello-world1":
        source => "puppet://$server/test1/hello-world1"
    }
}

class helloworld2 {
    file { "/tmp/hello-world2":
        source => "puppet://$server/test1/hello-world2"
    }
}
