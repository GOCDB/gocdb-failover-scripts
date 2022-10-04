#!/usr/bin/python3

"""
This file contains a script to check the GOCDB failover process is happening.

Specifically, it checks the log file passed as the first arguement for evidence
the process has suceeded / failed recently.

It assumes the log file is formatted as follows:
2022-10-04T09:40:01+0000
2022-10-04T09:40:01+0000 completed ok
2022-10-04T10:40:01+0000
2022-10-04T10:40:01+0000 completed ok
2022-10-04T11:40:01+0000
An Error
2022-10-04T12:40:01+0000
An Error
Another Error
2022-10-04T13:40:01+0000
2022-10-04T14:40:01+0000 completed ok
"""
from datetime import datetime, timedelta, timezone
import sys

# These are the return codes icinga expects.
RETURN_CODE_OK = 0
RETURN_CODE_WARNING = 1
RETURN_CODE_CRITICAL = 2
RETURN_CODE_UNKNOWN = 3

# This script will allow the latest run of the failover process to be this many
# minutes ago without returning RETURN_CODE_CRITICAL.
GRACE_PERIOD_MINUTES = 447

# The string the database update script outputs on a sucessful restore.
OK_STRING = "completed ok"

# Wrap everything in a try...except block so we can return RETURN_CODE_UNKNOWN
# on a unexpected failure.
try:
    # Use a inner try...except block to handle the more expected error of
    # "No file path provided" differently.
    try:
        log_file = sys.argv[1]
    except IndexError:
        print("No file path provided as the first argument")
        sys.exit(RETURN_CODE_UNKNOWN)

    # Extract the last line of the log file.
    # Use a inner try...except block to handle the more expected error of
    # "Couldn't open/read the provided file" differently.
    try:
        with open(log_file, 'r') as log_file:
            line_list = log_file.read().splitlines()
    except IOError:
        print("An error occured trying to open/read {0}".format(log_file))
        sys.exit(RETURN_CODE_CRITICAL)

    for line in reversed(line_list):
        # If OK_STRING is in the line we are looking at, we need to extract
        # the timestamp from that line to determine when the failover
        # process last succeeded.
        if OK_STRING in line:
            last_success_string = line.split(" ")[0]
            last_success_datetime = datetime.strptime(
                last_success_string,
                "%Y-%m-%dT%H:%M:%S%z"
            )

    print("The failover process last succeeded at %s." % last_success_datetime)

    # If the failover process hasn't suceeded in a while, the timestamp will be
    # old and we want to treat that as an error.
    grace_period_timedelta = timedelta(minutes=GRACE_PERIOD_MINUTES)
    grace_period_cutoff = datetime.now(timezone.utc) - grace_period_timedelta
    if last_success_datetime < grace_period_cutoff:
        sys.exit(RETURN_CODE_CRITICAL)

    # If we get here, it's all good man.
    sys.exit(RETURN_CODE_OK)

except Exception as error:
    print("An unexpected error occured: {0}".format(error))
    sys.exit(RETURN_CODE_UNKNOWN)
