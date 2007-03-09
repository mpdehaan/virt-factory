#!/bin/bash

/usr/bin/sqlite3 /var/lib/virt-factory/primary_db < /usr/share/virt-factory/db_schema/schema.sql
/usr/bin/sqlite3 /var/lib/virt-factory/primary_db < /usr/share/virt-factory/db_schema/populate.sql
