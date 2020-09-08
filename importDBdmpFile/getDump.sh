#!/bin/bash

# Set some things that cause this script to exit on a failure,
# rather than carry on blindly.
# -e Exit on any error
# -u Classify unset variables as errors
set -eu

# Get useful variables to refer to later in this script.
source /etc/gocdb/failover.sh

# Copy the DB dump file.
/usr/bin/scp $DB_DUMP_FROM $DB_DUMP_TO

# unset things to not affect the rest of the Failover process.
set +eu
