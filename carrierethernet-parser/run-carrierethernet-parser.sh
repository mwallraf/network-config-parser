#!/usr/local/bin/bash
export LC_ALL=C

## wrapper for ers-parser.py
## add -h to display additional help

ROOTDIR=$(dirname "$0")
cd $ROOTDIR

#source venv/bin/activate

SCRIPT=carrierethernet-parser.py
PYTHON=/usr/local/bin/python2.7

args=$@
$PYTHON bin/$SCRIPT $args

