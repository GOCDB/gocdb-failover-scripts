#!/bin/bash
# http://www.oracle-base.com/articles/misc/oracle-shell-scripting.php
# RESULT=$(sqlplus system/XXXXXXX <<EOF
# EXEC DBMS_STATS.gather_schema_stats('gocdb5');
# exit;
# EOF
# )
# echo $RESULT

# PASSFILE is in "parfile" format for impdp
PASSFILE=/root/importDBdmpFile/pass_file
USER_PASS=$(cat "${PASSFILE}" | grep "^userid=" | cut -d "=" -f 2)

# /nolog runs sqlplus without connecting to anything
# Having CONNECT in script keeps ${USER_PASS} off the commandline
# And hence not visible to "ps"
RESULT=$(sqlplus /nolog <<- ENDSQL
	CONNECT ${USER_PASS};
	EXEC DBMS_STATS.gather_schema_stats('gocdb5');
	EXIT;
	ENDSQL
)
echo $RESULT

# parse $RESULT to see if we got an error, looking for text error
#if [ grep -i $RESULT
