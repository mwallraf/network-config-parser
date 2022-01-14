#!/usr/local/bin/bash

## wrapper for ers-parser.py
## add -h to display additional help

ROOTDIR=$(dirname "$0")
SCRIPT=cpe-parser.py
PYTHON=$(which python2.7)

cd $ROOTDIR

args=$@
$PYTHON $ROOTDIR/bin/$SCRIPT $args

