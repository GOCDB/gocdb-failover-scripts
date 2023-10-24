#!/bin/bash

# Script for downloading the gocdb5 db dmp file and importing into the
# local oracle xe instance using sqlplus.
# Notes:
# - The updatelog.txt file is appended each time with log messages whenever the script is ran.
# - The last successfully .dmp file is stored in the 'lastImportedDmpFile' dir
#   under a file name with the datetime appended (creating a manual backup of the last imported .dmp file).
# - The script echos messages to the stdout if there is a failure for whatever reason and exits
#   with a non-zero return code.
# - No email is invoked from this script, but if the script is ran by e.g. cron.hourly, the cron
#   daemon will email the echoed messages for us when the script fails.
#
# David Meredith

# cd into dir where child scripts are located
cd /root/gocdb-failover-scripts/importDBdmpFile

#Setup our env vars
####################################
. ./ora11gEnvVars.sh

updatelog=./updateLog.txt

function logger {
  echo $*>> $updatelog
  # todo - add a function to email admins is issue occurs and invoke from above
  # /bin/mail -s 'gocdump is old' gocdb-admins@mailman.egi.eu < /etc/cron.hourly/gocdumpold.txt
}


#logger "hello world"
#exit


logger "==============Updating Log $(/bin/date) ================="

# Download the dmp file
####################################
getDumpOutput=`./getDump.sh 2>&1`
getDumpReturnCode=$?
#echo $getDumpOutput
if [ $getDumpReturnCode != 0 ]; then
  logger "wget failed [$getDumpReturnCode]"
  logger "$getDumpOutput"
  echo "wget failed [$getDumpReturnCode]"
  echo "$getDumpOutput"
  exit $getDumpReturnCode
  #exit 0
#else
#  logger "wget downloaded ok"
fi


# Drop gocdb user (gocdb5 user is recreated when doing the impdb)
####################################
dropGocdbUserOutput=`./dropGocdbUser2.sh 2>&1`
dropGocdbExitCode=$?
#echo $dropGocdbUserOutput
if [ $dropGocdbExitCode != 0 ]; then
  logger "Unknown error on drop gocdb user [$dropGocdbExitCode]"
  logger "$dropGocdbUserOutput"
  echo "Unknown error on drop gocdb user [$dropGocdbExitCode]"
  echo "$dropGocdbUserOutput"
  exit $dropGocdbExitCode
fi

# manually parse the output string for errors
#grepOutput=`grep -i error <<< $dropGocdbUserOutput`
grepOutput=$(echo $dropGocdbUserOutput | grep -i error)
grepResultCode=$?
if [ $grepResultCode = 0 ]; then
    # exit code of 0 means the string 'error' was matched
    logger "Dropping GOCDB5 user failed [$grepResultCode]"
    logger "$grepOutput"
    echo "Dropping GOCDB5 user failed [$grepResultCode]"
    echo "$grepOutput"
    exit 1
#else
#    logger "gocdb5 user dropped ok"
fi

# load the data using impdb
####################################
loadDataOutput=`./loadData.sh 2>&1`
loadDataExitCode=$?
#echo $loadDataOutput
if [ $loadDataExitCode != 0 ]; then
  logger "Unknown error on loadData [$loadDataExitCode]"
  logger "$loadDataOutput"
  echo "Unknown error on loadData [$loadDataExitCode]"
  echo "$loadDataOutput"
  exit $loadDataExitCode
fi

# manually parse the output string for errors
grepLoadDataOutput=$(echo $loadDataOutput | grep -i error)
grepLoadDataExitCode=$?
if [ $grepLoadDataExitCode = 0 ]; then
  # exit code of 0 means the string 'error' was matched
  logger "Load data failed [$grepLoadDataExitCode]"
  logger "$grepLoadDataOutput"
  echo "Load data failed [$grepLoadDataExitCode]"
  echo "$grepLoadDataOutput"
  exit 1;
#else
#  logger "loaded data ok"
fi

# gather stats
####################################
gatherStatsOutput=`./gatherStats.sh 2>&1`
gatherStatsExitCode=$?
#echo $gatherStatsOutput
if [ $gatherStatsExitCode != 0 ]; then
  logger "unknown error on gatherStats [$gatherStatsExitCode]"
  logger "$gatherStatsOutput"
  echo "unknown error on gatherStats [$gatherStatsExitCode]"
  echo "$gatherStatsOutput"
  exit $gatherStatsExitCode
fi

# manually parse the output string for errors
grepGatherStatsOutput=$(echo $gatherStatsOutput | grep -i error)
grepGatherStatsExitCode=$?
if [ $grepGatherStatsExitCode = 0 ]; then
  # exit code of 0 means the string 'error' was matched
  logger "gatherStats parsing failed [$grepGatherStatsExitCode]"
  logger "$grepGatherStatsOutput"
  echo "gatherStats parsing failed [$grepGatherStatsExitCode]"
  echo "$grepGatherStatsOutput"
  exit 1;
#else
#  logger "stats gathered ok"
fi


# Create a copy of the last successfully imported dmp file and
# store this in the lastImportedDmpFile dir with the time and date appended
# to the file name
if [ ! -d lastImportedDmpFile ]; then
  mkdir lastImportedDmpFile
fi

# cd into the dir (this directory must exist)
cd lastImportedDmpFile
cdReturnCode=$?
if [ $cdReturnCode != 0 ]; then
  logger "cd lastImportedDmpFile dir failed [$cdReturnCode]"
  exit $cdReturnCode
fi

dmpPrefix=_goc5dump_
dmpCopyExt=dmpcopied
dmpTargetFN=${dmpPrefix}$(date +%F_%R_%S)
dmpTarget=$dmpTargetFN.$dmpCopyExt

# copy the dmp file to the dump target
cp /tmp/goc5dump.dmp $dmpTarget
cpDmpReturnCode=$?
if [ $cpDmpReturnCode != 0 ]; then
  # cp failed so exit early as we don't want to overwrite
  exit $cpDmpReturnCode
fi

# delete existing .dmp backup files and move .dmpcopied to create latest/new .dmp file
rm -f ${dmpPrefix}*.dmp
mv $dmpTarget $dmpTargetFN.dmp

# and move back up a dir as before
cd ..

# Do not remove following lines - other processes rely on these exact
# strings being the last line in the relevant log file.
echo "$(date --iso-8601='seconds') INFO: completed ok"
logger "completed ok"
# Do not add any further "logger" statements after above line
