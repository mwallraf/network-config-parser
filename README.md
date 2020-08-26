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
           -v /output:/opt/network-discovery/output \
           mwallraf/network-config-parser:latest
```

