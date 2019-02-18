FROM python:slim

ADD https://github.com/oanda/oandapy/archive/master.tar.gz /tmp/oandapy.tar.gz
ADD . /tmp/oanda-cli

RUN set -e \
      && ln -sf /bin/bash /bin/sh

RUN set -e \
      && apt-get -y update \
      && apt-get -y dist-upgrade \
      && apt-get -y install --no-install-recommends --no-install-suggests \
        curl \
      && apt-get -y autoremove \
      && apt-get clean \
      && rm -rf /var/lib/apt/lists/*

RUN set -e \
      && pip install -U --no-cache-dir \
        pip /tmp/oandapy.tar.gz /tmp/oanda-cli \
      && rm -rf /tmp/oandapy.tar.gz /tmp/oanda-cli

ENTRYPOINT ["oanda-cli"]
