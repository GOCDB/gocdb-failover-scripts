# GOCDB Failover Automation Scripts/Dirs
Author: David Meredith + JK

[this ascii file is coded in "markdown" and is best viewed in a markdown enabled browser, see https://en.wikipedia.org/wiki/Markdown for more details]

This repo contains the service and cron scripts used to run a failover gocdb instance, includes the following dirs:
* autoEngageFailover/
  * Contians a Service script (```gocdb-autofailover.sh```) and child scripts that monitors the main production instance. If a prolonged outage is detected, the GOCDB top DNS alias 'goc.egi.eu' is swtiched from the production instance to the failover instance. This switch can also be performed manually when needed. 
* importDBdmpFile/
  * Contains a sript that should be invoked by cron hourly (```1_runDbUpdate.sh```) to download and install a .dmp of the production DB into the local failover DB. This runs separtely from the autoEngageFailover process. 
* nsupdate_goc/
  * Scripts for switching the DNS to/from the production/failover instance. 
* archiveDmpDownload/
  * Contains a script to download/archive dmp files in a separate process 

# Packages
* The following scripts needs to be installed and configuired for your installation: 
```
/root/
  autoEngageFailover/         # Scripts to mon the production instance and engage failover
      |_ gocdb-autofailover.sh# MAIN SERVICE SCRIPT to mon production instance
      |_ engageFailover.sh    #   Child script, run if prolonged outage is detected
      
  importDBdmpFile/            # Scripts download/install a .dmp of the prod data
      |_ 1_runDbUpdate.sh     # MAIN SCRIPT that can be called from cron, invokes child scripts below 
      |_ ora11gEnvVars.sh     #   Setup oracle env
      |_ getDump.sh           #   Download a .dmp of the production data 
      |_ dropGocdbUser.sh     #   Drops the current DB schema
      |_ loadData.sh          #   Load the last successfully downloaded DB dmp into the RDBMS
      |_ gatherStats.sh       #   Oracle gathers stats to re-index
      |_ pass_wgetrc_exemplar.txt #   Sample pwd file for getDump.sh (rename to pass_wgetrc) 
      |_ pass_file_exemplar.txt   #   Sample pwd file for DB (rename to pass_file)

  nsupdate_goc/              # Scripts for switching the DNS to the failover
      |_ goc_failover.sh     #   Points DNS to failover instance
      |_ goc_production.sh   #   Points DNS to production instance 

  archiveDmpDownload/        # Contains script to download/archive dmp files in a separate process e.g from cron.daily
      |_ archiveDump.sh      # Main script that dowloads dmp and saves in a sub-dir 
      |_ archive/            # Contains archive/dmp files 
```

## /root/autoEngageFailover/ 
Start in this dir. Dir contains the 'gocdb-autofailover.sh'
service script which should be installed as a service in
'/etc/init.d/gocdb-autofailover'. This service invokes
'engageFailover.sh' which monitors the production instance
with a ping-check. If a continued outage is detected;
the script starts the failover procedure which includes the
following: 
* the gocdb admins are emailed, 
* the age of the last successfully imported dmp file is
  checked to see that it is current, 
* the hourly cron that downloads the dmp file is stopped (see
  importDBdmpFile below), 
* <strike>symbolic links to the server cert/key are updated so they
  point to the 'goc.egi.eu' cert/key</strike> (note, no longer needed as cert contains dual SAN) 
* the dnscripts are invoked to change the dns (see
  nsupdate_goc below).  

## /root/importDBdmpFile/ 
Contains scripts that download the .dmp file and install this
dmp file into the local Oracle XE instance. The master script
is '1_runDbUpdate.sh' which needs to be invoked from an hourly
cron:   

```
# more /etc/cron.hourly/cronRunDbUpdate.sh
#!/bin/bash

/root/importDBdmpFile/1_runDbUpdate.sh
```

You will also need to modify the two password files to specify
your own pw ('pass_wgetrc' and 'pass_file'). These contain the
pw for the secure download of dmp file and the pw of the DB
system user. 
 
## /root/nsupdate_goc/
Contains the nsupdate keys and nsupdate scripts for switching
the 'goc.egi.eu' top level DNS alias to point to either the
production instance or the failover. 


## /root/archiveDmpDownload/
Contains a script that downloads the dmp file and stores the file in the archive/ sub-dir.
The script also deletes archived files that are older than 'x' days. 
This script can be called in a separate process, e.g. from cron.daily to build a 
set of backups. 


#Failover Instructions 
* Choose from options 1) 2) 3)

## To start/stop the auto failover service 
This will continuously monitor the production
instance and engage the failover automatically during prolonged outages

Run as a service:

```bash
chkconfig --list | grep gocdb-auto
/sbin/service gocdb-autofailover stop
/sbin/service gocdb-autofailover start
/sbin/service gocdb-autofailover status

```
  
Directly (not as a service): 

```bash
cd /root/autoEngageFailover
./gocdb-autofailover.sh {start|stop|restart}

```

## To manually engage the failover immediately 
E.g. for known/scheduled outages, run the following
passing 'now' as the first command-line argument:

Stop the service: 
```
service gocdb-autofailover stop
```
Or to stop if running manually: 
```
cd /root/autoEngageFailover
./gocdb-autofailover.sh stop
```
Engage the failover now:                                 
```
./engageFailover.sh now
```

## Restore failover service after failover was engaged
You will need to manually revert the steps executed by the
failover so the dns points back to the production instance
and restore/restart the failover process. This includes:   
* <strike>restore the symlinks to the goc.dl.ac.uk server cert and key
  (see details below)</strike> (no longer needed as cert contains dual SAN) 
* restore the hourly cron to download the dmp of the DB
* run nsupdate procedure to repoint 'goc.egi.eu' back to
  'gocdb-base.esc.rl.ac.uk'
  MUST read /root/nsupdate_goc/nsupdateReadme.txt. 
* restart the failover service

####Restore Walkthrough
At end of downtime (production instance ready to be restored) first re-point DNS: 

```bash
echo We first switch dns to point to production instance
cd /root/nsupdate_goc
./goc_production.sh

```

Now wait for DNS to settle, this takes approx **2hrs** and during this time the goc.egi.eu domain will 
swtich between the failover instance and the production instance. You should monitor this using nsupdate:  

```bash
nslookup goc.egi.eu
# check this returns the following output referring to
# next.gocdb.eu
	Non-authoritative answer:
	goc.egi.eu canonical name = next.gocdb.eu.
	Name: next.gocdb.eu
	Address: 130.246.143.160
```

After DNS has become stable the production instance will now be serving requests. 
Only after this ~2hr period should we re-start failover service:

```bash
echo First go check production instance and confirm it is up
echo running ok and that dns is stable
rm /root/autoEngageFailover/engage.lock
mv cronRunDbUpdate.sh /etc/cron.hourly   

# Below server cert change no longer needed as cert contains dual SAN
# This means a server restart is no longer needed. 
#echo Change server certificate and key back for goc.dl.ac.uk
#ln -sf /etc/pki/tls/private/goc.dl.ac.uk.key.pem /etc/pki/tls/private/hostkey.pem
#ln -sf /etc/grid-security/goc.dl.ac.uk.cert.pem /etc/grid-security/hostcert.pem
#service httpd restart
#service gocdb-autofailover start
#service gocdb-autofailover status
#  gocdb-autofailover is running... 
```

Now check the '/root/autoEngageFailover/pingCheckLog.txt' and
'/root/autoEngageFailover/errorEngageFailover.txt' files to
see that the service is running ok and pinging every ~10mins.
