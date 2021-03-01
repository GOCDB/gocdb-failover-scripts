#!/bin/bash

# Get useful variables to refer to later in this script.
source /etc/gocdb/failover.sh

# Copy the DB dump file.
/usr/bin/scp $DB_DUMP_FROM $DB_DUMP_TO

