#!/usr/bin/python 

import subprocess
import random

PW_FILE="/etc/virt-factory/dbaccess"  # must be chown postgres, chmod 550

DATABASE='vfdb'

CREATE_SCHEMA_SQL = """
    CREATE SCHEMA %(DATABASE)s;
    CREATE TABLE demo (foo text, bar text);
"""

CREATE_USER_SQL = """
    DELETE ROLE %(username)s;
    CREATE ROLE %(username)s LOGIN PASSWORD '%(password)s'
    NOINHERIT
    VALID UNTIL 'infinity';

    ALTER ROLE %(username)s SET search_path=%(DATABASE)s,public;
        
    GRANT usage ON SCHEMA %(DATABASE)s TO %(username)s;
    GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE demo TO %(username)s;
"""

def adduser(username,password):
    dvr = open("/dev/urandom","r")
    r = random.Random(dvr.read(255))
    dvr.close()
    password = "".join([ chr(x) for x in r.sample(range(ord('a'),ord('z')),10) ])
    pwf = open(PW_FILE, "w+")
    pwf.write(password)
    pwf.close()
    data = CREATE_USER_SQL % {
        "username"    : username,
        "password"    : password,
        "DATABASE"    : DATABASE
    }
    __runsql(data)

def createdb():
    data = CREATE_SCHEMA_SQL % { "DATABASE" : DATABASE }
    __runsql(data)
   
def __runsql(data):
    print data
    p = subprocess.Popen("psql --dbname %s" % (DATABASE), shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    (stdout, stderr) = p.communicate(data)

if __name__ == "__main__":
    createdb()
    adduser("foosball","foosball")


