# findhost-inventory

Findhost inventory script


## ABOUT
This scripts loads all backup configs from stepstone server, parses them and saves the output back to the stepstone server so that it can be used by findhost-consolidate script.

This is only a temporary solution because this script is failing on stepstone due to memory limits.


## RUNNING THE SCRIPT
bash run-py37.sh


## CRONTAB
The script is scheduled in the crontab of mwallraf:

## generate findhost file based on config files
## this script used to run on stepstone server however the server does
## not have sufficient memory
## config files are copied from stepstone, the script consolidates
## all data and saves the results back to stepstone
## - this is a temp solution -
0 7 * * * sh /opt/findhost-inventory/run-py37.sh
