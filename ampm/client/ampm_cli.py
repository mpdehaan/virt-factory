#!/usr/bin/python

# cli tool for accessing virt-factory functionality


# basic modes:
#     status
#     query
#     list
#     migrate
#     pause
#     resume
#     create

import ampmlib


import getopt
import os
import sys

import config

defaults = {"server":"http://127.0.0.1:5150",
            "user": "",
            "username": "admin",
            "password": "fedora" }

cfg = config.AmpmConfig(defaults)
cfg.load()




from command_modules import list
from command_modules import query
from command_modules import create
from command_modules import delete
from command_modules import add
from command_modules import pause


def print_help():
    print "== This is a useless help string blurb =="
    print

    
def main():

    
    username = cfg.get("user", "username")
    password = cfg.get("user", "password")
    server = cfg.get("server", "url")
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hvu:p:s:", [
            "help",
            "verbose",
            "username=",
            "password=",
            "server=",
            ])
    except getopt.error, e:
        print _("Error parsing command list arguments: %s") % e
        showHelp() 
        sys.exit(1)

    for (opt, val) in opts:
        if opt in ["-h", "--help"]:
            print_help()
            sys.exit()
        if opt in ["-v", "--verbose"]:
            verbose = 1
        if opt in ["-u", "--username"]:
            username = val
        if opt in ["-p", "--password"]:
            password = val
            # FIXME: munge sys.argv so password doesn't show up in ps, etc listings
        if opt in ["-s", "--server"]:
            server = val
            

    try:
        mode = args[0]
    except IndexError:
        print_help()
        sys.exit()


    if mode not in ["help", "list", "query", "create", "delete", "add", "pause"]:
        print_help()
        sys.exit()

    modeargs = args[args.index(mode)+1:]


    api = ampmlib.Api(url=server,
                      username=username,
                      password=password)

    
    if mode == "list":
        list.run(modeargs, api=api)

    if mode == "query":
        query.run(modeargs, api=api)

    if mode == "create":
        create.run(modeargs, api=api)

    if mode == "delete":
        delete.run(modeargs, api=api)

    if mode == "add":
        add.run(modeargs, api=api)

    if mode == "pause":
        pause.run(modeargs, api=api)

        
if __name__ == "__main__":
    main()

  
