# network-config-parser

Scripts that are used for parsing network equipment backup configs (ex Cisco routers). Useful facts or config details are parsed and stored in a single output file that can be easily used in grep functions.


## DOCKER

Build process:

```
docker build --tag mwallraf/network-config-parser:latest .
```

Start Docker:

```
docker run --detach --name network-config-parser \
  -v /opt/SCRIPTS/network-config-parser/output:/opt/network-config-parser/output \
  -v /opt/SCRIPTS/exscript-backup/configs:/opt/network-config-parser/router-parser/configs \
  -v /opt/SCRIPTS/network-config-parser/log:/opt/network-config-parser/log \
  -v /opt/SCRIPTS/network-config-parser/.env:/opt/network-config-parser/.env \
  -v /opt/SCRIPTS/network-config-parser/router-parser/.env:/opt/network-config-parser/router-parser/.env \
  mwallraf/network-config-parser:latest
```

