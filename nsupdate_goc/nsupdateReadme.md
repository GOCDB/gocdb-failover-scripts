# DNS Switch via nsupdate
This recipe describes the actions to carry in order to swap GOCDB top DNS
alias from one instance to another 
Author: David Meredith

DNS switching is used so that goc.egi.eu domain points to the failover at DL.
Note: 
* we have the nsupdate keys safe 
  * on gocdb-base.esc.rl.ac.uk in /root/nsupdate_goc 
  * on goc.dl.ac.uk in /root/nsupdate_goc 
* Updated nsupdate files for controlling 'goc.egi.eu' are given below  


##Actions (Please read all below to understand these actions)
* Logon as root on goc.dl.ac.uk or gocdb-base.esc.rl.ac.uk and cd to following dir
```
cd /root/nsupdate_goc
```

* Run goc_failover.sh to swich the dns to the failover 
```
[root@goc nsupdate_goc]# goc_failover.sh
```

* Or, run goc_production.sh to swich the dns back to the production instance   
```
[root@goc nsupdate_goc]# goc_production.sh
```

* After each dns switch youi can verify the settings have been applied on the dns server using:
```
nslookup goc.egi.eu ns.muni.cz
```

* And globally using: 
```
nslookup goc.egi.eu 
host goc.egi.eu
```

## Background
GOCDB top level DNS alias (goc.egi.eu) is maintained and operated by CESNET.
The alias points to the GOCDB production web server, and can be swapped 
between different instances in order to transparently bring up a replica server 
when the master is unreachable.

Swaping is only allowed with an authorised key.
Be aware that owning the key is vital to be able to change the entry 
for gog.egi.eu. Anybody who has them can do that using nsupdate with the nsupdate file below. 

The main script (goc_failover.sh) does a nsupdate command passing in the private key and 
using a 'here' document to redirect the config file into the command.  
Note, nsupdate with the -k option, nsupdate reads the shared secret from the file keyfile.  


