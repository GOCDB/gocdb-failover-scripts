#!/bin/bash

#service oracle-xe restart

# Script below will drop the gocdb5 user only if it exists
# rather than using a simple drop in the script:  drop user gocdb5 cascade;
#
# We drop the user because impdb will create the user for us (most DBAs let the impdb
# create the user - note, we need to use the imported user's pw).
# If the user already exists when we call impdb we get an error reporting the user already
# exists as described at:
# http://www.dba-oracle.com/t_ora_31684_import_impdp.htm
# Or, we can use 'exclude=user' in the impdb command as described at same link.
#
# http://www.oracle-base.com/articles/misc/oracle-shell-scripting.php
#
# Here doc: The minus sign after the << will ignore tab characters (Note: not all whitespace!)
# at the start of a line, so you can indent your data to increase the readability
#
# RESULT=$(sqlplus system/XXXXXXX <<- ENDSQL

# pass_file is in "parfile" format for impdp
USER_PASS=$(cat "pass_file" | grep "^userid=" | cut -d "=" -f 2)

# Need to exit gracefully if pass_file doesn't exist or
# above filter fails

# /nolog runs sqlplus without connecting to anything
# Having CONNECT in script keeps ${USER_PASS} off the commandline
# And hence not visible to "ps"
RESULT=$(sqlplus /nolog <<- ENDSQL
	CONNECT ${USER_PASS};
	create or replace directory dmpdir as '/tmp';
	DROP USER GOCDB5 CASCADE;
	EXIT;
	ENDSQL
)
echo $RESULT

# sample successfull $RESULT
#SQL*Plus: Release 11.2.0.2.0 Production on Fri Sep 27 14:28:37 2013 Copyright (c) 1982, 2011, Oracle. All rights reserved. Connected to: Oracle Database 11g Express Edition Release 11.2.0.2.0 - 64bit Production SQL> Directory created. SQL> 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 PL/SQL procedure successfully completed. SQL> Disconnected from Oracle Database 11g Express Edition Release 11.2.0.2.0 - 64bit Production

