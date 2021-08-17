#!/usr/bin/env python3
'''
Retrieve a mysqldump file from a given location on a remote host and use mysql
to import the database locally. The remote file can be compressed as a .zip
archive, in which case it is inflated. After successful load, the dump file
is archived.
'''
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
    '''
    Make accessible the parameters, configuration and set up logging
    '''
    def __init__(self, path):

        config = configparser.ConfigParser()

        config.read(path)

        self.remoteHost = config.get('remote', 'host')
        self.remoteUser = config.get('remote', 'user')
        self.remotePath = config.get('remote', 'path')

        self.workDir = config.get('local', 'workDir')
        self.archiveDir = config.get('local', 'archiveDir')
        self.mysqlOptionsPath = config.get('local', 'mysqloptions')
        self.format = config.get('local', 'format')
        self.noImport = config.get('local', 'noImport')
        self.retryCount = config.getint('local', 'retryCount')

        logging.basicConfig(filename=config.get('logs', 'file'),
                            format=config.get('logs', 'format'),
                            datefmt=config.get('logs', 'dateFormat'),
                            level=config.get('logs', 'level').upper())

        self.checkPerms(self.mysqlOptionsPath)

    def checkPerms(self, path):

        if not os.path.exists(path):
            raise Exception('mysql import options/password file: ' + path + ' does not exist. Import terminated.')

        # The password file must not be world-readable

        if (os.stat(path).st_mode & (os.R_OK | os.W_OK | os.X_OK) != 0):
            raise Exception('Open permissions found on database password file. Import terminated.')


def getConfig():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default='./importMariaDBdmpFile/config.ini', )

    args = parser.parse_args()

    if os.path.exists(args.config):
        return args

    raise Exception('Configuration file ' + args.config + ' does not exist')


def runCommand(args):
    '''
    Run the given argument array as a command
    '''

    logging.debug('running command:' + ' '.join(args))

    try:
        subprocess.check_output(args, stderr=subprocess.STDOUT, shell=False)

    except subprocess.CalledProcessError as p:
        logging.error('command failed: ' + ' '.join(args))
        raise Exception(p.output.rstrip())


def getDump(remoteUser, remoteHost, remotePath, localDir):
    '''
    Fetch the file from the remote and save it locally
    '''

    logging.debug('fetching remote file ... ')

    # there is clear text personal data in the dump so try to make sure the permissions are appropriate
    os.umask(0o077)

    # scp will replace the local file contents if it already exists
    # We do not run with '-q' to allow meaningful authentication error messages to be logged.
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
        zip = zipfile.ZipFile(localPath, 'r')
        zipContents = zip.namelist()
        if len(zipContents) != 1:
            raise Exception('Error: .zip archive must contain only 1 file.')
        logging.debug('inflating to ' + localDir)
        zip.extractall(localDir)
        localPath = localDir + '/' + zip.namelist()[0]
        logging.debug('inflated ' + localPath)
        zip.close
        logging.debug('zip archive inflation completed')

    return localPath


def importDB(optionsPath, importPath, retryCount):
    '''
    Use mysql to import the file
    '''
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
        except Exception as exc:
            logging.debug('mysql command import failed.')
            if count < retryCount:
                logging.error(str(sys.exc_info()[1]) + '. Retrying.')
                snooze = min(0.1 * (pow(2, count) - 1), 20)
                logging.debug('sleeping (' + '{:.2f}'.format(snooze) + 'secs)')
                sleep(snooze)
                logging.debug('retry ' + str(count) + ' of ' + str(retryCount))
                # insert backoff time wait here
                pass
            else:
                logging.debug('exceeded retry count for database load failures')
                raise exc

    logging.debug('database load completed')


def archiveDump(importPath, archive, format):
    '''
    Save the dump file in the archive directory
    '''

    logging.debug('archiving dump file ...')

    if not os.path.isdir(archive):
        raise Exception('Archive directory ' + archive + ' does not exist.')

    archivePath = archive + '/' + strftime(format, gmtime())

    logging.debug('moving ' + importPath + ' to ' + archivePath)

    shutil.move(importPath, archivePath)

    logging.debug('removing all .dmp files in ' + archive)

    for oldDump in glob.iglob(archive + '/*.dmp'):
        os.remove(oldDump)

    shutil.move(archivePath, archivePath + '.dmp')

    logging.debug('moving ' + archivePath + ' to ' + archivePath + '.dmp')

    logging.debug('archive completed')


def main():

    try:
        args = getConfig()

        cnf = Conf(args.config)

        if os.path.isfile(cnf.noImport):
            logging.error(cnf.noImport + ' exists. No import attempted. File contents -')
            with open(cnf.noImport) as f:
                logging.error(f.read().rstrip())
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
