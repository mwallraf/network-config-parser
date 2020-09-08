# If you want to import files with different env vars this may be a good place
# to import
# . /etc/some_file_with_env_vars

echo "start router-parser script"

# if you want to run the script directly then these are the minimal required vars
if [[ -z $ROUTER_PARSER_CONFIG_FOLDER ]]; then
  . .env
  SCRIPTDIR=$(dirname "${BASH_SOURCE[0]}")
  ROUTER_PARSER_DIR=$SCRIPTDIR

  echo "ENV -> $ENV"
  echo "SCRIPTDIR -> $SCRIPTDIR"
  echo "ROUTER PARSER DIR -> $ROUTER_PARSER_DIR"
  echo "working dir = `pwd`"
  echo "ROUTER_PARSER_CONFIG_FOLDER -> $ROUTER_PARSER_CONFIG_FOLDER"

fi

# export so that it can be used by python
export ENV
export VERBOSE
export DEBUG
export ROUTER_PARSER_CONFIG_FOLDER
export ROUTER_PARSER_LOG_FOLDER
export ROUTER_PARSER_LOGFILE
export ROUTER_PARSER_OUTPUT_FOLDER
export ROUTER_PARSER_MAX_CONFIG_AGE

FINALOUTPUT="$ROUTER_PARSER_OUTPUT_FOLDER/output.csv"
TMPOUTPUT="$FINALOUTPUT.tmp"
MINEXPECTEDLINES=1000
TODAY=`date +"%Y-%m-%d"`

# run the script and store the output to a temp file
python $ROUTER_PARSER_DIR/router-parser.py > $TMPOUTPUT

# only if the output has to be combined with the output of network-discovery
# this links CE_HOSTNAME to hostname
# and removes unnecessary columns from the network-discovery output
# the network-discovery output column names will also be prepended by DISC_
if [[ ! -z ${ADD_NETWORK_DISCOVERY_INFO} ]]; then
  python $ROUTER_PARSER_DIR/add-network-discovery.py --router-parser-result="$TMPOUTPUT" --network-discovery-result="$NETWORK_DISCOVERY_FILE" --output-file="$TMPOUTPUT.join"
  mv "$TMPOUTPUT.join" $TMPOUTPUT
fi

# if the temp file has at least the minimal amount of lines then 
if [ $(wc -l "$TMPOUTPUT" | sed -e 's/^[[:space:]]*//' | cut -d" " -f1) -ge $MINEXPECTEDLINES ]; then

	# if the output file alread exists then store the backup
	if [[ -f "$FINALOUTPUT" ]]; then
		cp $FINALOUTPUT "$FINALOUTPUT.$TODAY"
	fi

    mv $TMPOUTPUT $FINALOUTPUT
fi





