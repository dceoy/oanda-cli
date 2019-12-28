FROM python:slim AS builder

ADD . /tmp/oanda-cli

RUN set -e \
      && apt-get -y update \
      && apt-get -y dist-upgrade \
      && apt-get -y install --no-install-recommends --no-install-suggests \
        gcc libc-dev

RUN set -e \
      && pip install -U --no-cache-dir pip /tmp/oanda-cli

FROM python:slim

COPY --from=builder /usr/local /usr/local

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

ENTRYPOINT ["/usr/local/bin/oanda-cli"]
