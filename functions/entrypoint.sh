## Docker entrypoint to create the crontab scheduler

#!/bin/bash

# Start the run once job.
echo "Docker container has been started"

# Setup a cron schedule
echo "0 6,20 * * * /bin/bash /opt/network-config-parser/parser.sh --router-parser parse >> /var/log/cron.log 2>&1
@weekly rm -rf /var/log/cron.log
# This extra line makes it a valid cron" > scheduler.txt

crontab scheduler.txt
crond -f

