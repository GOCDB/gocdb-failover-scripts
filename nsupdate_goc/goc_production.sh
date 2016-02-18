echo "changing goc.egi.eu DNS record at ns.mui.cz to next.gocdb.eu"
echo
nsupdate -k goc.egi.eu_ns.muni.cz_key.conf  <<EOF
server ns.muni.cz
zone egi.eu
update delete goc.egi.eu. CNAME
update add goc.egi.eu. 60 CNAME next.gocdb.eu.
show
send
EOF
echo 
echo "verifying the change ..."
echo
nslookup goc.egi.eu ns.muni.cz
