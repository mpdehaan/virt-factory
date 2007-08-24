#!/usr/bin/python


import os
import ConfigParser



class AmpmConfig(ConfigParser.SafeConfigParser):
    def __init__(self, defaults=None):
        ConfigParser.SafeConfigParser.__init__(self, defaults)

        # I'm not a fan of the configParser default stuff
        self.set_ampm_defaults()

    def load(self):
        filename = os.path.expanduser("~/.ampm_config")
        if os.access(filename, os.R_OK):
            self.readfp(open(filename))
        else:
            print "no config file found"

    def set_ampm_defaults(self):
        self.add_section("server")
        self.add_section("user")
        self.set("server", "url", "http://127.0.0.1:5150")
        self.set("user", "username", "admin")
        self.set("user", "password", "fedora")
        


if __name__ == "__main__":
    foo = AmpmConfig()

    foo.add_section("section1")
    foo.add_section("section2")

    foo.set("section1", "url", "http://127.0.0.1/vf")
    foo.set("section2", "username", "admin")
    foo.set("section2", "password", "fedora")

    fo = open("/tmp/test-config", "w")
    foo.write(fo)
    fo.close()

    bar = AmpmConfig()
    bar.readfp(open("/tmp/test-config"))

    for section in bar.sections():
        print section
        print bar.items(section)

    
