#!/usr/bin/python3

"""
This file contains a script to check the GOCDB failover process is happening.

Specifically, it checks the log file passed as the first arguement for evidence
the process has suceeded / failed recently.

It assumes the log file is formatted as follows:
2021-08-02T08:40:01+0000
An Error
2021-08-02T09:40:01+0000
An Error
Another Error
2021-08-02T10:40:01+0000
2021-08-02T11:40:01+0000
2021-08-02T12:40:01+0000
2021-08-02T13:40:01+0000
2021-08-02T14:40:01+0000
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
GRACE_PERIOD = 70

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
            lines = log_file.read().splitlines()
            last_line = lines[-1]
    except IOError:
        print("An error occured trying to open/read {0}".format(log_file))
        sys.exit(RETURN_CODE_CRITICAL)

    # Convert the last line of the log to a timestamp.
    # Use a inner try...except block to handle the somewhat more expected error
    # of "the failover process ran, but something went wrong" differently.
    try:
        last_success = datetime.strptime(last_line, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        print("An error occured: {0}".format(last_line))
        sys.exit(RETURN_CODE_CRITICAL)

    print("The failover process last suceeded at %s" % last_success)
    # If the failover process hasn't suceeded in a while, the timestamp will be
    # old and we want to treat that as an error.
    if last_success < (datetime.now(timezone.utc) - timedelta(minutes=GRACE_PERIOD)):
        sys.exit(RETURN_CODE_CRITICAL)

    # If we get here, it's all good man.
    sys.exit(RETURN_CODE_OK)

except Exception as error:
    print("An unexpected error occured: {0}".format(error))
    sys.exit(RETURN_CODE_UNKNOWN)
