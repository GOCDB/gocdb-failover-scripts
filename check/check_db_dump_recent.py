#!/usr/bin/python3

"""
This file contains a script to check the GOCDB failover process is happening.

Specifically, it checks the log file passed as the first argument for evidence
the process has succeeded recently.
"""
from datetime import datetime, timedelta
import sys

# These are the return codes icinga expects.
RETURN_CODE_OK = 0
RETURN_CODE_WARNING = 1
RETURN_CODE_CRITICAL = 2
RETURN_CODE_UNKNOWN = 3


class CheckDBDumpRecent():

    def __init__(self, grace_period):
        # This script will not return a critical error code unless the last
        # successful run was this long ago.
        self.GRACE_PERIOD = grace_period

        # The string the database update script outputs on a successful restore.
        self.OK_STRING = "completed ok"

    def run(self, log_file_path):
        # Wrap everything in a try...except block so we can return
        # RETURN_CODE_UNKNOWN on a unexpected failure.
        try:
            # Extract the last line of the log file.
            # Use a inner try...except block to handle the more expected error
            # of "Couldn't open/read the provided file" differently.
            try:
                with open(log_file_path, 'r') as log_file:
                    line_list = log_file.read().splitlines()
            except IOError:
                print(
                    "An error occured trying to open/read {0}".format(
                        log_file_path
                    )
                )

                return RETURN_CODE_CRITICAL

            # Assume the failover process has never run, then attempt to
            # disprove that by looping through the logs.
            last_success = None
            for line in reversed(line_list):
                # If OK_STRING is in the line we are looking at, we need to extract
                # the timestamp from that line to determine when the failover
                # process last succeeded.
                if self.OK_STRING in line:
                    last_success_timestamp = line.split(" ")[0]
                    last_success = datetime.strptime(
                        last_success_timestamp,
                        "%Y-%m-%dT%H:%M:%S+0000",
                    )
                    # We only want the most recent success, so once we have
                    # found it, break out of this loop
                    break

            if last_success is None:
                print(
                    "The failover process has never succeeded, "
                    "according to %s." % (
                        log_file_path
                    )
                )
                return RETURN_CODE_CRITICAL

            print("The failover process last succeeded at %s" % last_success)
            # If the failover process hasn't succeeded in a while, the
            # timestamp will be old and we want to treat that as an error.
            if last_success < (datetime.now() - self.GRACE_PERIOD):
                return RETURN_CODE_CRITICAL

            # If we get here, it's all good man.
            return RETURN_CODE_OK

        except Exception as error:
            print("An unexpected error occured: {0}".format(error))
            return RETURN_CODE_UNKNOWN


if __name__ == "__main__":
    # Handle error when no file path is provided.
    try:
        log_file = sys.argv[1]
    except IndexError:
        print("No file path provided as the first argument")
        sys.exit(RETURN_CODE_UNKNOWN)

    checker = CheckDBDumpRecent(grace_period=timedelta(hours=7))
    # Run the checker and report the status code back.
    sys.exit(checker.run(log_file))
