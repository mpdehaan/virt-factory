# hello-world.pp

class test1164 {
    file { "/tmp/hello-world1":
        source => "puppet://$server/Test1_x86_64/hello-world1"
    }
}

class test1164 {
    file { "/tmp/hello-world2":
        source => "puppet://$server/Test1_x86_64/hello-world2"
    }
}
