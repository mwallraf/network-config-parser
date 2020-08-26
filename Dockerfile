FROM alpine:3.12.0

ARG TZ='Europe/Brussels'

ENV TZ ${TZ}

RUN apk update

RUN apk add --no-cache bash python3 py3-pip py3-virtualenv py3-yaml tzdata procps

# Create the network-discovery folder
RUN mkdir -p /opt/network-discovery
RUN chmod -R 755 /opt/network-discovery

# Add files
ADD . /opt/network-config-parser
ADD functions/entrypoint.sh /entrypoint.sh

RUN chmod -R 755 /entrypoint.sh
RUN chmod -R 755 /opt/network-config-parser/parser.sh
RUN chmod -R 755 /opt/network-config-parser/router-parser/run.sh

ENTRYPOINT /entrypoint.sh

