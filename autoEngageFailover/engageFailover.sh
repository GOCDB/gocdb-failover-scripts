#!/bin/bash

# Usage: ./autoEnageFailover.sh [now]
# where now is optional. If 'now' is specified as the first cmd line arg, then
# the failover is engaged immediately rather than on detection of a prolongued outage.
#
# Script will fail early if the lockFile from previous engage is present.
#
# Note, after the main instance has been restored, you will need to manually
# do the following steps:
# Revert this swap:
# ln -s /etc/pki/tls/private/gocdb.hartree.stfc.ac.uk.key.pem /etc/pki/tls/private/hostkey.pem
# ln -s /etc/grid-security/gocdb.hartree.stfc.ac.uk.cert.pem /etc/grid-security/hostcert.pem
#
# Restore hourly cron job:
# mv /root/cronRunDbUpdate.sh /etc/cron.hourly/


# ====================Setup Variables===========================
# setup log files
updateLog=/root/autoEngageFailover/pingCheckLog.txt
errorEngageFailoverLog=/root/autoEngageFailover/errorEngageFailoverLog.txt
lockFile=/root/autoEngageFailover/engage.lock

# Dir containing the import DB scripts and log file
importDBdmpFile=/root/importDBdmpFile

# maintainthe current fail count
failcount=0

# server certificate / key
# note, in production we will use the gocdb.hartree.stfc.ac.uk server/host cert and key which has no
# password protecting the private key.
userkey="/etc/pki/tls/private/gocdb.hartree.stfc.ac.uk.key.pem"
usercert="/etc/grid-security/gocdb.hartree.stfc.ac.uk.cert.pem"

# URL to monitor for the main production instance
pingUrl="https://goc.egi.eu/portal/GOCDB_monitor/ops_monitor_check.php"

# An external url to check that local network can reach outside
externalPingUrl="http://google.co.uk"

# number of secs between re-pings (600secs = 10mins)
sleepTime=600s

# number of successive fails before invoking failover (30 * 10mins = 300mins = 5hrs)
failCountLimit=30

# email subject and to address for notification that failover is engaged
SUBJECT="gocdb failover warning"
TO="some.body@world.com,a.n.other@world.com"

# Determine whether to engage the failover immediately
ENGAGENOW="false"

# =====================================================

# Start script

# if first command line arg was 'now' then ENGAGENOW=true
if [ -n "$1" ] ; then
        if [ $1 == "now" ] ; then
          ENGAGENOW="true"
        fi
fi


# email all given args to $TO
function email {
/bin/mail -s "$SUBJECT" "$TO" <<EOF
Time: `date`
$*
EOF
}


# log all given args to the udpate log
function logger {
  echo $*>> $updateLog
}
function errorLogger {
  echo $*>> $errorEngageFailoverLog
}


# Ping the pingUrl(goc) and pingUrl2(external).
# If can't ping pingUrl2(external), then return 0 for ok (don't want to engage failover
#  if can't ping outside world - prob site network error)
# If can ping pingUrl2(external), then ping pingUrl(goc) and echo
#  its return code (0 for ok, (+ve) int for an error code)
# Also write any ping success and error output to the logger and errorLogger
function pingcheck {
    #pingOut=$(curl -k --key $userkey --cert $usercert $pingUrl 2>&1)
    # Use -q flag for quiet mode, and tell wget to output to stdout with O-
    pingOut=$(wget -qO- --no-check-certificate --private-key $userkey --certificate $usercert $pingUrl 2>&1)
    local pingCode=$?
    # check an external site to ensure its not a local network issue
    pingOut2=$(wget -qO- $externalPingUrl 2>&1)
    local pingCode2=$?

    if [ $pingCode2 != 0 ]; then
      # can't ping external site, prob a site network, therefore
      # return 0 to indicate ok (don't want to engage failover if site network issue)
      errorLogger "can't ping external site"
      errorLogger $pingOut2
      echo 0
    else
       if [ $pingCode != 0 ]; then
          errorLogger "Goc ping failed $(date)"
          errorLogger $pingOut
          # echo a return value to be captured using command substitution with: $(pingcheck)
          # Note, using command subsitution to run this function causes the func to run in a sub-shell
          # so we can't update and global variables from within this function !
          echo $pingCode
       else
          # can ping external and goc
          logger "ping ok, external and goc: $(date)"
          echo 0
       fi
    fi
}




# test previous lock file don't already exist, fail if it does !
if [ -f "$lockFile" ]; then
  echo "Error, lock file from previous failover-engage exists, to startup delete: $lockFile"
  exit 0
fi




# Create the log if it don't already exist
touch $updateLog
touch $errorEngageFailoverLog
logger "==============================Starting up $(date)====================================="
errorLogger "===================================Starting up $(date)=================================="

# loop if not engaging now
if [ $ENGAGENOW == "false" ] ; then
	# loop while global failcount is less than x
	while [ $failcount -lt $failCountLimit ]
	do
	    pingCode=$(pingcheck)
	    if [ $pingCode != 0 ]; then
		# if ping failed then increment failcount
		(( failcount++ ))
	    else
		# else if ping worked re-set failcount (back) to zero
		failcount=0
		#logger "ping ok $(date) : $pingUrl"
	    fi

	    #echo "failcount is: $failcount, pingcode is: $pingCode"
	    sleep $sleepTime
	done
fi


# 'N' consecutive failures encountered. Next invoke failover script
# =================================================================

# - log the date
errorLogger "=============Start Failover Swtich================="
errorLogger "Detected successive failues on $(date)"
errorLogger "Starting engage failover"

email "Detected successive failures. Attempting to engage the failover - please see the logs: $updateLog $errorEngageFailoverLog"

# While developing, force an exit here (will have to practice below using
# the provided test.egi.eu goc domain)
#exit 0



# - Test that the last goc.dmp imported ok by parsing /root/importDBdmpFile/updateLog.txt
#cd /root/importDBdmpFile
cd $importDBdmpFile
if [ "$(tail -1 ./updateLog.txt)" != "completed ok" ]; then
  errorLogger "Last import of dmp file did not complete ok, exiting auto-failover early before cert and dns switch "
  exit 1
fi

errorLogger "Attempting to move cron"

# - Move hourly cron job to disable (don't want this to execute while in failover mode)
mv /etc/cron.hourly/cronRunDbUpdate.sh /root

errorLogger "Swapping server certs"

## - Swap server cert
## Not needed e.g. if your server cert has a dual SAN
#unlink /etc/grid-security/hostcert.pem
#unlink /etc/pki/tls/private/hostkey.pem
#ln -s /etc/grid-security/goc.egi.eu.cert.pem /etc/grid-security/hostcert.pem
#ln -s /etc/pki/tls/private/goc.egi.eu.key.pem /etc/pki/tls/private/hostkey.pem
## note, after the main instance has been restored, you will need to revert this swap:
## ln -s /etc/pki/tls/private/gocdb.hartree.stfc.ac.uk.key.pem /etc/pki/tls/private/hostkey.pem
## ln -s /etc/grid-security/gocdb.hartree.stfc.ac.uk.cert.pem /etc/grid-security/hostcert.pem

#errorLogger "After server cert swap"


#errorLogger "Changing DNS"
#cd /root/nsupdate_goc
#
#
#errorLogger "Running nsupdate script"
#nsupdateOut=$(./goc_failover.sh 2>&1)
#nsupdateCode=$?
#errorLogger "nspdateCode was: $nsupdateCode"
#errorLogger "nsupdateOut was: $nsupdateOut"
#if [ $nsupdateCode != 0 ]; then
#  errorLogger "nsupdate Failed"
#  # dont need to exit, restart apache won't hurt anyway
#  #exit $nsupdateCode
#fi
#
#
## Restart apache
#errorLogger "Restarting apache"
#service httpd restart


# Finally create the lockFile to indicate the failover ran ok
touch $lockFile

email "Failover script completed"

# End
errorLogger "==========================End failover switch======================="
