# hello-world.pp

class test11 {
    file { "/tmp/hello-world1":
        source => "puppet://$server/Test1/hello-world1"
    }
}

class test12 {
    file { "/tmp/hello-world2":
        source => "puppet://$server/Test1/hello-world2"
    }
}
