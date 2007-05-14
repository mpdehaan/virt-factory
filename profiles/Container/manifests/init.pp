# hello-world.pp

class helloworld1 {
    file { "/tmp/hello-world1":
        source => "puppet://$servername/Container/hello-world1"
    }
}

class helloworld2 {
    file { "/tmp/hello-world2":
        source => "puppet://$servername/Container/hello-world2"
    }
}
