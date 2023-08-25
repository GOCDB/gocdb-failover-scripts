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

    def run(self, log_file_path):
        # Wrap everything in a try...except block so we can return
        # RETURN_CODE_UNKNOWN on a unexpected failure.
        try:
            # Extract the last line of the log file.
            # Use a inner try...except block to handle the more expected error
            # of "Couldn't open/read the provided file" differently.
            try:
                with open(log_file_path, 'r') as log_file_path:
                    lines = log_file_path.read().splitlines()
                    last_line = lines[-1]
            except IOError:
                print(
                    "An error occured trying to open/read {0}".format(
                        log_file_path
                    )
                )

                return RETURN_CODE_CRITICAL

            # Convert the last line of the log to a timestamp.
            # Use a inner try...except block to handle the somewhat more
            # expected error of "the failover process ran, but something
            # went wrong" differently.
            try:
                last_success = datetime.strptime(
                    last_line,
                    "%Y-%m-%dT%H:%M:%S%z",
                )
            except ValueError:
                print("An error occured: {0}".format(last_line))
                return RETURN_CODE_CRITICAL

            print("The failover process last suceeded at %s" % last_success)
            # If the failover process hasn't suceeded in a while, the
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
