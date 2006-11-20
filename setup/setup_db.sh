#!/bin/sh
mkdir -p /opt/shadowmanager
sqlite3 /opt/shadowmanager/primary_db < schema.sql
