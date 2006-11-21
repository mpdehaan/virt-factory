#!/bin/sh
mkdir -p /opt/shadowmanager
# constants we need for deployment
sqlite3 /opt/shadowmanager/primary_db < populate.sql
# filler values that just help out humans during development
sqlite3 /opt/shadowmanager/primary_db < demodata.sql
