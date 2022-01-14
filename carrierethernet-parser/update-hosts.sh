#!/bin/bash

##
## Update the /etc/hosts/10-observium file with the latest IP addresses of all carrier ethernet devices
## Updates can ONLY be done if the hosts file already exists (for reasons of security)
##

ROOTDIR=$(dirname "$0")
cd ${ROOTDIR}

#INVENTORY=output/general.inventory.csv
INVENTORY=output/hosts
HOSTSFILE=/etc/hosts.d/10-carrierethernet
MINIMUMFILELENGTH=250   # minimum of devices present in the file
FILELENGTH=`wc -l ${INVENTORY} | cut -d" " -f1`

if [ ! -f ${INVENTORY} ]; then
    echo "Inventory file not found! Exit script."
    exit
fi

if [ "${FILELENGTH}" -le "${MINIMUMFILELENGTH}" ]; then
    echo "There should be at least ${MINIMUMFILELENGTH} hosts in the inventory file. Exit script."
    exit
fi

##
## create a new file for the carrier ethernet devices
## destination = /etc/hosts.d/10-carrierethernet
##
#echo "## CARRIER ETHERNET" > ${HOSTSFILE}
#tail -n +2 ${INVENTORY} | awk -F, '{ print $2 " " $1}' >> ${HOSTSFILE}

cp $INVENTORY $HOSTSFILE
