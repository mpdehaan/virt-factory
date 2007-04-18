#!/bin/sh
sqlite3 /var/lib/virt-factory/primary_db < ./service/db/schema/populate.sql
