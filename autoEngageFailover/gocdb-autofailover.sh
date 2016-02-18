#!/bin/bash
#
# Bring up/down the script to auto engage the gocdb failover
#
# chkconfig: 2345 99 1
# description: start/stop the auto failover script to swtich the DNS to point goc.egi.eu to the 
# goc.dl.ac.uk failover instance.
#
# Usage: ./gocdb-autofailover.sh {start|stop|restart|status}

LOCATION=/root/autoEngageFailover
SCRIPT=engageFailover.sh
LOGFILE=gocdb-autofailover-log
LOCKFILE=/var/lock/subsys/gocdb-autofailover

# start the service 
start() {
        if [ -e $LOCKFILE ]
        then
        echo "gocdb-autofailover LOCK File is Present..."
        else
        $LOCATION/$SCRIPT 1>> $LOCATION/$LOGFILE  2>> $LOCATION/$LOGFILE &
        sleep 1
        ps aux | grep $SCRIPT | grep -v grep &> /dev/null && touch $LOCKFILE && echo "gocdb-autofailover started successfully..." || echo "gocdb-autofailover failed to start..."
        fi
}

# Stop the service
stop() {
        if [ -e $LOCKFILE ]
        then
        ps aux | grep $SCRIPT | grep -v grep | kill -s 9 `awk {'print $2'}` &> /dev/null
        test $? == 0 && echo "gocdb-autofailover stopped successfully..." || echo "gocdb-autofailover is not running but LOCK file is present.
Deleting LOCK File..."
        rm -f $LOCKFILE
        else
        echo "gocdb-autofailover LOCK File is not Present - can't stop service cleanly, please check..."
        fi
}
# check on the status 
status() {
        ps aux | grep $SCRIPT | grep -v grep &> /dev/null && echo "gocdb-autofailover is running..."
        test $? != 0 && echo "gocdb-autofailover is not running..."
}


### main logic ###
case "$1" in
  start)
        start
        ;;
  stop)
        stop
        ;;
  status)
        status
        ;;
  restart)
        stop
        start
        ;;
  *)
        echo $"Usage: $0 {start|stop|restart}"
        exit 1
esac
exit 0

