#!/usr/bin/python

import subprocess
import random

######################################
# CONFIG SECTION

# must be chown postgres, chmod 550
DATABASE      = "virtfactory"
PW_FILE       = "/etc/virt-factory/dbaccess"  
SCHEMA_FILE   = "/var/lib/virt-factory/db_schema/schema.sql"
POPULATE_FILE = "/var/lib/virt-factory/db_schema/populate.sql"

######################################

def createdb():
    dvr = open("/dev/urandom","r")
    r = random.Random(dvr.read(255))
    dvr.close()
    password = "".join([ chr(x) for x in r.sample(range(ord('a'),ord('z')),10) ])
    pwf = open(PW_FILE, "w+")
    pwf.write(password)
    pwf.close()

    sf = open(SCHEMA_FILE, "r")
    data = sf.read() % { "password" : password }
    __runsql(data)

def populate():
    data = open(POPULATE_FILE, "r")
    __runsql(data)

def initialize_upgrade_path():
    p = subprocess.Popen("/usr/bin/vf_upgrade_db --initialize", shell=True)
    p.communicate()
   
def __runsql(data):
    print data
    p = subprocess.Popen("psql --dbname %s" % (DATABASE), shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (stdout, stderr) = p.communicate(data)

if __name__ == "__main__":
    createdb()
    initialize_upgrade_path()
    populate()



