FROM alpine:3.12.0

ARG TZ='Europe/Brussels'

ENV TZ ${TZ}

RUN apk update

RUN apk add --no-cache bash python3 python3-dev py3-pip py3-virtualenv tzdata procps lapack libstdc++ g++ gcc gfortran musl-dev lapack-dev

# create an alias for python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Create the network-config-parser folder
RUN mkdir -p /opt/network-config-parser
RUN chmod -R 755 /opt/network-config-parser

# Add files
ADD . /opt/network-config-parser
ADD functions/entrypoint.sh /entrypoint.sh

# install python requirements
RUN pip install -r /opt/network-config-parser/requirements.txt

RUN chmod -R 755 /entrypoint.sh
RUN chmod -R 755 /opt/network-config-parser/parser.sh
RUN chmod -R 755 /opt/network-config-parser/router-parser/run.sh

WORKDIR /opt/network-config-parser

ENTRYPOINT /entrypoint.sh

