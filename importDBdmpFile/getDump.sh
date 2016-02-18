#!/bin/bash

# seems that curl don't return a 0 exit code when it fails to download successfully, see: 
# http://superuser.com/questions/590099/can-i-make-curl-fail-with-an-exitcode-different-than-0-if-the-http-status-code-i
# 
#curl --capath /etc/grid-security/certificates -u failover:kugA7Rer https://goc.egi.eu/dbDump/goc5dump.dmp -o /tmp/goc5dump.dmp

# therefore use wget which does return 0 exit code if downloaded ok
# /usr/bin/wget -O /tmp/goc5dump.dmp --user failover --password u_LK28_B2fv_dm --no-check-certificate https://goc.egi.eu/dbDump/goc5dump.dmp

DUMPDIR=/tmp
BASEDIR=/root/importDBdmpFile

export WGETRC=$BASEDIR/pass_wgetrc

/usr/bin/wget --no-check-certificate \
	--ca-directory /etc/grid-security/certificates \
	-O $DUMPDIR/goc5dump.dmp \
	https://goc.egi.eu/dbDump/goc5dump.dmp
