#!/usr/bin/env python3
"""
Fetch and install a database dump file.

Retrieve a mysqldump file from a given location on a remote host and use mysql
to import the database locally. The remote file can be compressed as a .zip
archive, in which case it is inflated. After successful load, the dump file
is archived.
"""
import argparse
import configparser
import glob
import logging
import os
import shutil
import subprocess
import sys
from time import gmtime, strftime, sleep
import zipfile


class Conf:
    """Wrapper class for the config parameters."""

    def __init__(self, path):
        """Read in the parameters, configuration and set up logging."""
        config = configparser.ConfigParser()

        config.read(path)

        self.mysqlOptionsPath = path

        self.remoteHost = config.get('remote', 'host')
        self.remoteUser = config.get('remote', 'user')
        self.remotePath = config.get('remote', 'path')

        self.workDir = config.get('local', 'workDir')
        self.archiveDir = config.get('local', 'archiveDir')
        self.format = config.get('local', 'format')
        self.noImport = config.get('local', 'noImport')
        self.retryCount = config.getint('local', 'retryCount')

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

        # Ensure all python log times are expressed in UTC, for simplicity and
        # consistency with other timestamps in the relevant log files.
        logging.Formatter.converter = gmtime

        checkPerms(self.mysqlOptionsPath)


def checkPerms(path):
    """Check security of permissions on the configuration file with password."""
    if not os.path.exists(path):
        raise Exception('mysql import options/password file: '
                        + path
                        + ' does not exist. Import terminated.')

    # The password file must not be world-readable

    if os.stat(path).st_mode & (os.R_OK | os.W_OK | os.X_OK) != 0:
        raise Exception('Open permissions found on database password file. Import terminated.')


def getConfig():
    """Set up the single argument."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='./importMariaDBdmpFile/config.ini', )

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
        raise Exception(pErr.output.rstrip()) from pErr


def getDump(remoteUser, remoteHost, remotePath, localDir):
    """Fetch the file from the remote and save it locally."""
    logging.debug('fetching remote file ... ')

    # there is clear text personal data in the dump so try to make
    # sure the permissions are appropriate
    os.umask(0o077)

    if remoteUser == '' and remoteHost == '':
        # Just a local copy
        args = ['/usr/bin/cp',
                remotePath,
                localDir
                ]
    else:
        # scp will replace the local file contents if it already exists
        # We do not run with '-q' to allow meaningful authentication
        # error messages to be logged.
        args = ['/usr/bin/scp',
                '-o', 'PasswordAuthentication=no',
                remoteUser + '@' + remoteHost + ':' + remotePath,
                localDir
                ]

    runCommand(args)

    logging.debug('remote fetch completed')

    localPath = localDir + '/' + os.path.basename(remotePath)

    suffix = os.path.splitext(localPath)[1]

    if suffix == '.zip':
        logging.debug('inflating fetched zip archive ...')
        archive = zipfile.ZipFile(localPath, 'r')
        zipContents = archive.namelist()
        if len(zipContents) != 1:
            raise Exception('Error: .zip archive must contain only 1 file.')
        logging.debug('inflating to %s', localDir)
        archive.extractall(localDir)
        localPath = localDir + '/' + archive.namelist()[0]
        logging.debug('inflated %s', localPath)
        archive.close()
        logging.debug('zip archive inflation completed')

    return localPath


def importDB(optionsPath, importPath, retryCount):
    """Use mysql to import the file."""
    # Tested using dump generated using the command
    # > mysqldump --databases --lock-tables --dump-date \
    #             --add-locks -p gocdb -r /tmp/dbdump.sql

    args = ['/usr/bin/mysql',
            '--defaults-extra-file=' + optionsPath,
            '-e SOURCE ' + importPath
            ]

    count = 0

    while count < retryCount:
        count += 1
        try:
            logging.debug('loading database from dump file ...')
            runCommand(args)
            break
        except subprocess.CalledProcessError as exc:
            logging.debug('mysql command import failed.')
            if count < retryCount:
                logging.error('%s. Retrying.', str(sys.exc_info()[1]))
                snooze = min(0.1 * (pow(2, count) - 1), 20)
                logging.debug('sleeping (%s secs)', f'{snooze:.2f}')
                sleep(snooze)
                logging.debug('retry %s of %s', str(count), str(retryCount))
            else:
                logging.debug('exceeded retry count for database load failures')
                raise exc

    logging.debug('database load completed')


def archiveDump(importPath, archive, timeFormat):
    """Save the dump file in the archive directory."""
    logging.debug('archiving dump file ...')

    if not os.path.isdir(archive):
        raise Exception('Archive directory ' + archive + ' does not exist.')

    logging.debug('removing all .dmp files in %s', archive)

    for oldDump in glob.iglob(archive + '/*.dmp'):
        os.remove(oldDump)

    archivePath = archive + '/' + strftime(timeFormat, gmtime()) + '.dmp'

    logging.debug('moving ' + importPath + ' to ' + archivePath)

    shutil.move(importPath, archivePath)

    logging.debug('archive completed')


def main():
    """Execute the program."""
    try:
        args = getConfig()

        cnf = Conf(args.config)

        if os.path.isfile(cnf.noImport):
            logging.error('%s exists. No import attempted. File contents -', cnf.noImport)
            with open(cnf.noImport, encoding='utf-8') as fileText:
                logging.error(fileText.read().rstrip())
            return 1

        dump = getDump(cnf.remoteUser, cnf.remoteHost, cnf.remotePath, cnf.workDir)

        importDB(cnf.mysqlOptionsPath, dump, max(1, cnf.retryCount))

        archiveDump(dump, cnf.archiveDir, cnf.format)

        logging.info('completed ok')
        return 0

    except Exception:
        logging.error(sys.exc_info()[1])
        return 1


if __name__ == '__main__':
    sys.exit(main())
