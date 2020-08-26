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

# run the script

python $ROUTER_PARSER_DIR/findhost-inventory.py > "$ROUTER_PARSER_OUTPUT_FOLDER/output.csv"

