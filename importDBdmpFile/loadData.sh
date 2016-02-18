#!/bin/bash

# This import script imports gocdb5 schema and remaps this to the gocdb5 schema. 
# impdp system/XXXXX schemas=gocdb5 directory=dmpdir dumpfile=goc5dump.dmp remap_tablespace=GOCDB5:users table_exists_action=replace logfile=impGocDump.log

impdp parfile=/root/importDBdmpFile/pass_file schemas=gocdb5 \
	directory=dmpdir dumpfile=goc5dump.dmp \
	remap_tablespace=GOCDB5:users table_exists_action=replace \
	logfile=impGocDump.log

#Sample successful output: 

#Import: Release 11.2.0.2.0 - Production on Fri Sep 27 14:29:44 2013
#
#Copyright (c) 1982, 2009, Oracle and/or its affiliates.  All rights reserved.
#
#Connected to: Oracle Database 11g Express Edition Release 11.2.0.2.0 - 64bit Production
#Master table "SYSTEM"."SYS_IMPORT_SCHEMA_01" successfully loaded/unloaded
#Starting "SYSTEM"."SYS_IMPORT_SCHEMA_01":  system/******** schemas=gocdb5 directory=dmpdir dumpfile=goc5dump.dmp remap_tablespace=GOCDB5:users table_exists_action=replace logfile=impGocDump.log
#Processing object type SCHEMA_EXPORT/USER
#Processing object type SCHEMA_EXPORT/SYSTEM_GRANT
#Processing object type SCHEMA_EXPORT/ROLE_GRANT
#Processing object type SCHEMA_EXPORT/DEFAULT_ROLE
#Processing object type SCHEMA_EXPORT/PRE_SCHEMA/PROCACT_SCHEMA
#Processing object type SCHEMA_EXPORT/SEQUENCE/SEQUENCE
#Processing object type SCHEMA_EXPORT/TABLE/TABLE
#Processing object type SCHEMA_EXPORT/TABLE/TABLE_DATA
#. . imported "GOCDB5"."DOWNTIMES"                        1.157 MB   11722 rows
#. . imported "GOCDB5"."DOWNTIMES_ENDPOINTLOCATIONS"      644.0 KB   54000 rows
#. . imported "GOCDB5"."SERVICES"                         513.7 KB    4582 rows
#. . imported "GOCDB5"."USERS"                            306.3 KB    2293 rows
#. . imported "GOCDB5"."SITES"                            243.3 KB     650 rows
#. . imported "GOCDB5"."ROLES"                            115.7 KB    3316 rows
#. . imported "GOCDB5"."CERTIFICATIONSTATUSLOGS"          75.14 KB     552 rows
#. . imported "GOCDB5"."ENDPOINTLOCATIONS"                73.17 KB    4582 rows
#. . imported "GOCDB5"."SERVICES_SCOPES"                  54.60 KB    4583 rows
#. . imported "GOCDB5"."CERTIFICATIONSTATUSES"            5.546 KB       5 rows
#. . imported "GOCDB5"."COUNTRIES"                        7.414 KB      84 rows
#. . imported "GOCDB5"."INFRASTRUCTURES"                  5.515 KB       4 rows
#. . imported "GOCDB5"."NGIS"                             11.60 KB      38 rows
#. . imported "GOCDB5"."NGIS_SCOPES"                      5.882 KB      38 rows
#. . imported "GOCDB5"."OWNEDENTITIES"                    14.83 KB     726 rows
#. . imported "GOCDB5"."PROJECTS"                         6.304 KB       1 rows
#. . imported "GOCDB5"."PROJECTS_NGIS"                    5.882 KB      38 rows
#. . imported "GOCDB5"."ROLETYPES"                        5.898 KB      16 rows
#. . imported "GOCDB5"."SCOPES"                           6.031 KB       4 rows
#. . imported "GOCDB5"."SERVICEGROUPS"                    10.39 KB      37 rows
#. . imported "GOCDB5"."SERVICEGROUPS_SCOPES"             5.921 KB      37 rows
#. . imported "GOCDB5"."SERVICEGROUPS_SERVICES"           8.484 KB     253 rows
#. . imported "GOCDB5"."SERVICETYPES"                     15.71 KB      96 rows
#. . imported "GOCDB5"."SITES_SCOPES"                     12.43 KB     651 rows
#. . imported "GOCDB5"."SUBGRIDS"                         6.031 KB       7 rows
#. . imported "GOCDB5"."TIERS"                            5.476 KB       3 rows
#. . imported "GOCDB5"."TIMEZONES"                        7.187 KB      90 rows
#. . imported "GOCDB5"."ARCHIVEDNGIS"                         0 KB       0 rows
#. . imported "GOCDB5"."ARCHIVEDSERVICEGROUPS"                0 KB       0 rows
#. . imported "GOCDB5"."ARCHIVEDSERVICES"                     0 KB       0 rows
#. . imported "GOCDB5"."ARCHIVEDSITES"                        0 KB       0 rows
#. . imported "GOCDB5"."PRIMARYKEYS"                          0 KB       0 rows
#. . imported "GOCDB5"."RETRIEVEACCOUNTREQUESTS"              0 KB       0 rows
#Processing object type SCHEMA_EXPORT/TABLE/INDEX/INDEX
#Processing object type SCHEMA_EXPORT/TABLE/CONSTRAINT/CONSTRAINT
#Processing object type SCHEMA_EXPORT/TABLE/INDEX/STATISTICS/INDEX_STATISTICS
#Processing object type SCHEMA_EXPORT/TABLE/CONSTRAINT/REF_CONSTRAINT
#Processing object type SCHEMA_EXPORT/TABLE/STATISTICS/TABLE_STATISTICS
#Job "SYSTEM"."SYS_IMPORT_SCHEMA_01" successfully completed at 14:29:54

