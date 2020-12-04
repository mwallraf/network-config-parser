# Run the CarrierEthernet script (to parse SAOS based config files)
# Override parameters by creating a local .env file

echo "start carrier-ethernet script"

# if you want to run the script directly then these are the minimal required vars
if [[ -z $CARRIERETHERNET_PARSER_CONFIG_FOLDER ]]; then
  . .env
  SCRIPTDIR=$(dirname "${BASH_SOURCE[0]}")
  CARRIERETHERNET_PARSER_DIR=$SCRIPTDIR

  echo "ENV -> $ENV"
  echo "SCRIPTDIR -> $SCRIPTDIR"
  echo "CARRIER ETHERNET PARSER DIR -> $CARRIERETHERNET_PARSER_DIR"
  echo "working dir = `pwd`"
  echo "CARRIERETHERNET_PARSER_CONFIG_FOLDER -> $CARRIERETHERNET_PARSER_CONFIG_FOLDER"

fi


# export so that it can be used by python
export ENV
export VERBOSE
export DEBUG
export CARRIERETHERNET_PARSER_DIR
export CARRIERETHERNET_PARSER_CONFIG_FOLDER
export CARRIERETHERNET_PARSER_LOG_FOLDER
export CARRIERETHERNET_PARSER_LOGFILE
export CARRIERETHERNET_PARSER_OUTPUT_FOLDER
export CARRIERETHERNET_PARSER_MAX_CONFIG_AGE

FINALOUTPUT="$ROUTER_PARSER_OUTPUT_FOLDER/$ROUTER_PARSER_OUTPUT_FILE"
TMPOUTPUT="$FINALOUTPUT.tmp"
MINEXPECTEDLINES=1000
TODAY=`date +"%Y-%m-%d"`

# run the script and store the output to the output folder
args=$@
python $CARRIERETHERNET_PARSER_DIR/bin/carrierethernet-parser.py ${args}


# remove files older than 30 days
for d in "$CARRIERETHERNET_PARSER_LOG_FOLDER" "$CARRIERETHERNET_PARSER_OUTPUT_FOLDER"
do
  echo "remove old files in folder $d"
  find $d -type f -mtime +30
done

echo "end carrier-ethernet script"





