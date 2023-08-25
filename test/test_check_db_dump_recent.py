#!/usr/bin/python3

"""
This file tests the script that checks the GOCDB failover process is
happening.
"""

from datetime import datetime, timedelta
import os
import tempfile
import unittest

# Need to import the module as a whole to monkey patch the underlying
# datetime.now() calls.
import check.check_db_dump_recent


class TestCheckDBDumpRecent(unittest.TestCase):
    """
    This class tests the check.check_db_dump_recent module.

    For ORACLE test cases, the example log format is as follows:
        YYYY-MM-DDTHH:MM:SS+0000
        YYYY-MM-DDTHH:MM:SS+0000 INFO: completed ok
        YYYY-MM-DDTHH:MM:SS+0000
        An Error
        YYYY-MM-DDTHH:MM:SS+0000
        2023-01-01T11:41:01+0000 INFO: completed ok

    The example log formats follow the style of the actual logs generated.
    That is to say, an attempt to restore the database dump:
      - Starts with an ISO 8601 timestamp, this is because the restore is
      triggered by a cron job based off quattor cron jobs.
      - Ends with either (generated from the 1_runDbUpdate.sh):
        - an error with no timestamp
        - an ISO 8601 timestamp and the string "INFO: completed ok"

    For MariaDB test cases, the example log format is as follows:
        YYYY-MM-DDTHH:MM:SS+0000
        YYYY-MM-DDTHH:MM:SS+0000 INFO: completed ok
        YYYY-MM-DDTHH:MM:SS+0000
        YYYY-MM-DDTHH:MM:SS+0000 ERROR: An Error
        YYYY-MM-DDTHH:MM:SS+0000
        YYYY-MM-DDTHH:MM:SS+0000 INFO: completed ok

    The example log formats follow the style of the actual logs generated.
    That is to say, an attempt to restore the database dump:
      - Starts with an ISO 8601 timestamp, this is because the restore is
      triggered by a cron job based off quattor cron jobs.
      - Ends with an ISO 8601 timestamp followed by either (generated by
        failover_import.py):
        - an error
        - the string "INFO: completed ok"
    """

    def setUp(self):
        self.test_checker = check.check_db_dump_recent.CheckDBDumpRecent(
            grace_period=timedelta(
                minutes=30
            )
        )

        # Create and close a temporary log file for use in the tests.
        temp_file, self.temp_file_path = tempfile.mkstemp()
        os.close(temp_file)

        # Monkey patch the datetime module within check.check_db_dump_recent
        # so we don't have to worry about hard coded datetimes in these tests.
        check.check_db_dump_recent.datetime = MonkeyDateTime

    def tearDown(self):
        os.remove(self.temp_file_path)

    def _run_test(self, log_line_list, expected_return_code):
        """A helper function to run the checker, checking the return code."""
        # Write the individual log lines to self.temp_file_path.
        self._list_to_temp_file(log_line_list)

        return_code = self.test_checker.run(self.temp_file_path)

        self.assertEqual(
            return_code,
            expected_return_code,
            "Expected code %s, but got %s." % (
                expected_return_code,
                return_code,
            ),
        )

    def test_recent_success_mariadb(self):
        """Tests the check script given a recent, successful, run."""
        log_line_list = [
            "2023-01-01T09:40:01+0000",
            "2023-01-01T09:41:01+0000 ERROR: An Error",
            "2023-01-01T10:40:01+0000",
            "2023-01-01T10:41:01+0000 ERROR: An Error",
            "2023-01-01T10:42:01+0000 ERROR: Another Error",
            "2023-01-01T11:40:01+0000",
            "2023-01-01T11:41:01+0000 INFO: completed ok",
        ]

        self._run_test(log_line_list, check.check_db_dump_recent.RETURN_CODE_OK)

    def test_recent_failure_mariadb(self):
        """Tests the check script given a recent, unsuccessful, run."""
        log_line_list = [
            "2023-01-01T09:40:01+0000",
            "2023-01-01T09:41:01+0000 ERROR: An Error",
            "2023-01-01T10:40:01+0000",
            "2023-01-01T10:41:01+0000 ERROR: An Error",
            "2023-01-01T10:42:01+0000 ERROR: Another Error",
            "2023-01-01T11:40:01+0000",
            "2023-01-01T11:41:01+0000 INFO: completed ok",
            "2023-01-01T11:50:01+0000",
            "2023-01-01T11:51:01+0000 ERROR: Yet another Error",
        ]

        self._run_test(log_line_list, check.check_db_dump_recent.RETURN_CODE_OK)

    def test_old_success_mariadb(self):
        """Test the check script given an old, successful, run."""
        log_line_list = [
            "2023-01-01T09:40:01+0000",
            "2023-01-01T09:41:01+0000 INFO: completed ok",
            "2023-01-01T10:40:01+0000",
            "2023-01-01T10:41:01+0000 ERROR: An Error",
            "2023-01-01T10:42:01+0000 ERROR: Another Error",
            "2023-01-01T11:40:01+0000",
            "2023-01-01T11:41:01+0000 ERROR: Yet Another Error",
        ]

        self._run_test(log_line_list, check.check_db_dump_recent.RETURN_CODE_CRITICAL)

    def test_never_successful_mariadb(self):
        """Test the check script given a lack of success, ever."""
        log_line_list = [
            "2023-01-01T09:40:01+0000",
            "2023-01-01T09:41:01+0000 ERROR: An Error",
            "2023-01-01T10:40:01+0000",
            "2023-01-01T10:41:01+0000 ERROR: An Error",
            "2023-01-01T10:42:01+0000 ERROR: Another Error",
            "2023-01-01T11:40:01+0000",
            "2023-01-01T11:41:01+0000 ERROR: Yet another Error",
        ]

        self._run_test(log_line_list, check.check_db_dump_recent.RETURN_CODE_CRITICAL)

    def test_recent_success_oracle(self):
        """Tests the check script given a recent, successful, run."""
        log_line_list = [
            "2023-01-01T08:40:01+0000",
            "2023-01-01T08:41:01+0000 INFO: completed ok",
            "2023-01-01T09:40:01+0000",
            "An Error",
            "2023-01-01T10:40:01+0000",
            "An Error",
            "Another Error",
            "2023-01-01T11:40:01+0000",
            "2023-01-01T11:41:01+0000 INFO: completed ok",
        ]

        self._run_test(log_line_list, check.check_db_dump_recent.RETURN_CODE_OK)

    def test_recent_failure_oracle(self):
        """Tests the check script given a recent, unsuccessful, run."""
        log_line_list = [
            "2023-01-01T08:40:01+0000",
            "2023-01-01T08:41:01+0000 INFO: completed ok",
            "2023-01-01T09:40:01+0000",
            "An Error",
            "2023-01-01T10:40:01+0000",
            "An Error",
            "Another Error",
            "2023-01-01T11:40:01+0000",
            "2023-01-01T11:41:01+0000 INFO: completed ok",
            "2023-01-01T11:50:01+0000",
            "Yet another Error",
        ]

        self._run_test(log_line_list, check.check_db_dump_recent.RETURN_CODE_OK)

    def test_old_success_oracle(self):
        """Test the check script given an old, successful, run."""
        log_line_list = [
            "2023-01-01T09:40:01+0000",
            "2023-01-01T09:41:01+0000 INFO: completed ok",
            "2023-01-01T10:40:01+0000",
            "An Error",
            "Another Error",
            "2023-01-01T11:40:01+0000",
            "Yet Another Error",
        ]

        self._run_test(log_line_list, check.check_db_dump_recent.RETURN_CODE_CRITICAL)

    def test_never_successful_oracle(self):
        """Test the check script given a lack of success, ever."""
        log_line_list = [
            "2023-01-01T09:40:01+0000",
            "An Error",
            "2023-01-01T10:40:01+0000",
            "An Error",
            "Another Error",
            "2023-01-01T11:40:01+0000",
            "Yet another Error",
        ]

        self._run_test(log_line_list, check.check_db_dump_recent.RETURN_CODE_CRITICAL)

    def test_empty_log(self):
        """Test the check script given an empty input."""
        log_line_list = []

        self._run_test(log_line_list, check.check_db_dump_recent.RETURN_CODE_CRITICAL)

    def _list_to_temp_file(self, input_list):
        """Take the given list and write it to self.temp_file_path."""
        with open(self.temp_file_path, "w") as temp_file:
            for line in input_list:
                temp_file.write(line + "\n")


class MonkeyDateTime(datetime):
    """
    A class to monkey patch the datetime class.

    It subclasses the datetime class so should behave exactly like it, except
    that "now" is statically defined.
    """
    @classmethod
    def now(cls, tz=None):
        return cls(
            year=2023,
            month=1,
            day=1,
            hour=12,
        )


if __name__ == "__main__":
    unittest.main()
