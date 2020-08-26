#!/bin/bash -e
#
# Generic Shell Script Skeleton.
# Copyright (c) {{ YEAR }} - {{ AUTHOR }} <{{ AUTHOR_EMAIL }}>
#
# Built with shell-script-skeleton v0.0.3 <http://github.com/z017/shell-script-skeleton>

# Import common utilities
source "$(dirname "${BASH_SOURCE[0]}")/functions/common.sh"

# Import python env
# source "$(dirname "${BASH_SOURCE[0]}")/venv/bin/activate"

# Import local config if it exists
if [[ -f "$(dirname "${BASH_SOURCE[0]}")/.env" ]]; then
  source "$(dirname "${BASH_SOURCE[0]}")/.env"
fi

readonly SCRIPTDIR=$(dirname "${BASH_SOURCE[0]}")

#######################################
# SCRIPT CONSTANTS & VARIABLES
#######################################

# Script version
readonly VERSION=0.0.2

# List of required tools, example: REQUIRED_TOOLS=(git ssh)
readonly REQUIRED_TOOLS=()

# Long Options. To expect an argument for an option, just place a : (colon)
# after the proper option flag.
readonly LONG_OPTS=(help version router-parser)

# Short Options. To expect an argument for an option, just place a : (colon)
# after the proper option flag.
readonly SHORT_OPTS=hvd

# Script name
readonly SCRIPT_NAME=${0##*/}

# Define temp folders and other locations
readonly ROUTER_PARSER_DIR="$SCRIPTDIR/router-parser"
readonly ROUTER_PARSER="$ROUTER_PARSER_DIR/run.sh"

# switch that decides if the router-processor script has to run
declare RUN_ROUTER_PARSER=
declare SHOWHELP=true


#######################################
# SCRIPT CONFIGURATION CONSTANTS
#######################################

# the postprocessor script should be a bash script with execute permissions
if [[ -z ${ENV} ]]; then
  readonly ENV="PROD"
fi


#######################################
# help command
#######################################
function help_command() {
  cat <<END;

ABOUT:
  Start config parser scripts, existing scripts:
  - router-parser = parse ios based router scripts and try to link configs
                    based on P2P ip addresses

USAGE:
  $SCRIPT_NAME [options] <command>

OPTIONS:
  --help, -h              Alias help command
  --version, -v           Alias version command
  --router-parser         Start the router-parser script (default=no)
  --                      Denotes the end of the options.  Arguments after this
                          will be handled as parameters even if they start with
                          a '-'.

COMMANDS:
  parse                   Start the main parser script
  help                    Display detailed help
  version                 Print version information.

END
  exit 1
}

#######################################
# version command
#######################################
function version_command() {
  echo "$SCRIPT_NAME version $VERSION"
}



#######################################
# default command
#######################################
function default_command() {
  # set default command here
  if [ ${SHOWHELP} ]; then
    help_command
  fi
}



#######################################
# runs the parser script
#######################################
function start_parsing() {

  SHOWHELP=

echo "working dir = `pwd`"

  echo "--- Start the router-parser script ---"
  SECONDS=0

  if [ ${RUN_ROUTER_PARSER} ]; then

    start_router_parser

  fi  

  echo "--- The script has taken $SECONDS seconds to finish ---"

echo "working dir = `pwd`"
  
}



#######################################
# runs the router-parser script
#######################################
function start_router_parser() {

    . $ROUTER_PARSER

}


#######################################
# create temp folders
#######################################
function create_dirs()
{
    # remove the existing temp folders:
    #rm -rf "$DISCOVERYDIR"

    # create temp folders
    echo "create_dirs"
}

#######################################
# generate discovery hosts file and cleanup
# if SNMP polling is enabled then the output
# of the SNMP result is used, otherwise
# the ping file
#######################################
function cleanup()
{

    echo "cleanup"

}


#######################################
#
# MAIN
#
#######################################
function main() {
  # Required tools
  required $REQUIRED_TOOLS

  # Parse options
  while [[ $# -ge $OPTIND ]] && eval opt=\${$OPTIND} || break
        [[ $opt == -- ]] && shift && break
        if [[ $opt == --?* ]]; then
          opt=${opt#--}; shift

          # Argument to option ?
          OPTARG=;local has_arg=0
          [[ $opt == *=* ]] && OPTARG=${opt#*=} && opt=${opt%=$OPTARG} && has_arg=1

          # Check if known option and if it has an argument if it must:
          local state=0
          for option in "${LONG_OPTS[@]}"; do
            [[ "$option" == "$opt" ]] && state=1 && break
            [[ "${option%:}" == "$opt" ]] && state=2 && break
          done
          # Param not found
          [[ $state = 0 ]] && OPTARG=$opt && opt='?'
          # Param with no args, has args
          [[ $state = 1 && $has_arg = 1 ]] && OPTARG=$opt && opt=::
          # Param with args, has no args
          if [[ $state = 2 && $has_arg = 0 ]]; then
            [[ $# -ge $OPTIND ]] && eval OPTARG=\${$OPTIND} && shift || { OPTARG=$opt; opt=:; }
          fi

          # for the while
          true
        else
          getopts ":$SHORT_OPTS" opt
        fi
  do
    case "$opt" in
      # List of options
      v|version)    version_command; exit 0; ;;
      h|help)       help_command ;;
      router-parser) RUN_ROUTER_PARSER=true ;;
      force)        FORCE=true ;;
      # Errors
      ::)   err "Unexpected argument to option '$OPTARG'"; exit 2; ;;
      :)    err "Missing argument to option '$OPTARG'"; exit 2; ;;
      \?)   err "Unknown option '$OPTARG'"; exit 2; ;;
      *)    err "Internal script error, unmatched option '$opt'"; exit 2; ;;
    esac
  done
  readonly FORCE
  readonly RUN_ROUTER_PARSER
  shift $((OPTIND-1))

  # No more arguments -> call default command
  [[ -z "$1" ]] && default_command

  # Set command and arguments
  command="$1" && shift
  args="$@"

  # Execute the command
  case "$command" in
    # help
    help)     help_command ;;

    # version
    version)  version_command ;;

    # start the discovery
    parse) start_parsing ;;

    # Unknown command
    *)  err "Unknown command '$command'"; exit 2; ;;
  esac
}
#######################################
# Run the script
#######################################
main "$@"