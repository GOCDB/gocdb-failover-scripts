#!/usr/bin/env python3
"""
Perform a dump of a (remote) database and save locally.

Use the mysqldump utility to execute a (remote) database dump
and store the result locally, keeping a copy of the previous dump.
"""
import argparse
import configparser
import logging
import os
import shutil
import subprocess
import sys


class Conf:
    """Wrapper class for the config parameters."""

    def __init__(self, path):
        """Read in the parameters, configuration and set up logging."""
        config = configparser.ConfigParser(allow_no_value=True)

        config.read(path)

        self.mysqlOptionsPath = path

        self.resultFile = config.get('client-mariadb', 'result-file')

        self.noFetch = config.get('local', 'noFetch')
        self.dumpFile = config.get('local', 'dumpFile')
        self.databaseName = config.get('local', 'databaseName')

        logfile = config.get('logs', 'file')

        if logfile == '':
            logging.basicConfig(stream=sys.stdout,
                                format=config.get('logs', 'format'),
                                datefmt=config.get('logs', 'dateFormat'),
                                level=config.get('logs', 'level').upper())
        else:
            logging.basicConfig(filename=logfile,
                                format=config.get('logs', 'format'),
                                datefmt=config.get('logs', 'dateFormat'),
                                level=config.get('logs', 'level').upper())

        checkPerms(self.mysqlOptionsPath)


def checkPerms(path):
    """Check security of permissions on the configuration file with password."""
    if not os.path.exists(path):
        raise Exception('mysqldump options/password file: '
                        + path
                        + ' does not exist. Import terminated.')

    # The password file must not be world-readable

    if os.stat(path).st_mode & (os.R_OK | os.W_OK | os.X_OK) != 0:
        raise Exception('Open permissions found on database password file. Import terminated.')


def getConfig():
    """Set up the single argument."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='./fetchMariaDBdmpFile/failover_fetch.ini')

    args = parser.parse_args()

    if os.path.exists(args.config):
        return args

    raise Exception('Configuration file ' + args.config + ' does not exist')


def runCommand(args):
    """Run the given argument array as a command."""
    logging.debug('running command: %s', ' '.join(args))

    try:
        subprocess.check_output(args, stderr=subprocess.STDOUT, shell=False)

    except subprocess.CalledProcessError as pErr:
        logging.error('command failed: %s', ' '.join(args))
        raise Exception(pErr.stdout.rstrip()) from pErr


def runDump(mysqlOptionsPath, databaseName):
    """Run the dump."""
    logging.debug('running mysqldump ... ')

    args = ['/usr/bin/mysqldump',
            '--defaults-extra-file=' + mysqlOptionsPath,
            databaseName]

    runCommand(args)

    logging.debug('mysqldump completed')


def archiveDump(resultFile, dumpFile):
    """Archive the dump file."""
    logging.debug('archiving dump ...')

    destination = dumpFile + '_old'

    if os.path.exists(destination):
        os.remove(destination)

    if os.path.exists(dumpFile):
        shutil.move(dumpFile, destination)

    shutil.move(resultFile, dumpFile)

    logging.debug('archive completed ')


def main():
    """Execute the program."""
    try:
        args = getConfig()

        cnf = Conf(args.config)

        if os.path.isfile(cnf.noFetch):
            logging.error('%s exists. No fetch attempted. File contents -', cnf.noFetch)
            with open(cnf.noFetch, encoding='utf-8') as fileText:
                logging.error(fileText.read().rstrip())
            return 1

        runDump(cnf.mysqlOptionsPath, cnf.databaseName)

        archiveDump(cnf.resultFile, cnf.dumpFile)

        logging.info('completed ok')
        return 0

    except Exception:
        logging.error(sys.exc_info()[1])
        return 1


if __name__ == '__main__':
    sys.exit(main())
