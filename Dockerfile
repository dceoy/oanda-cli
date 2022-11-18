FROM ubuntu:latest

ENV DEBIAN_FRONTEND noninteractive

ADD https://bootstrap.pypa.io/get-pip.py /tmp/get-pip.py
ADD . /tmp/oanda-cli

RUN set -e \
      && ln -sf bash /bin/sh \
      && ln -s python3 /usr/bin/python

RUN set -e \
      && apt-get -y update \
      && apt-get -y dist-upgrade \
      && apt-get -y install --no-install-recommends --no-install-suggests \
        apt-transport-https ca-certificates curl python3 \
        python3-distutils \
      && apt-get -y autoremove \
      && apt-get clean \
      && rm -rf /var/lib/apt/lists/*

RUN set -e \
      && /usr/bin/python3 /tmp/get-pip.py \
      && pip install -U --no-cache-dir pip /tmp/oanda-cli \
      && rm -rf /tmp/oanda-cli

RUN set -e \
      && unlink /usr/lib/ssl/openssl.cnf \
      && echo -e 'openssl_conf = default_conf' > /usr/lib/ssl/openssl.cnf \
      && echo >> /usr/lib/ssl/openssl.cnf \
      && cat /etc/ssl/openssl.cnf >> /usr/lib/ssl/openssl.cnf \
      && echo >> /usr/lib/ssl/openssl.cnf \
      && echo -e '[default_conf]' >> /usr/lib/ssl/openssl.cnf \
      && echo -e 'ssl_conf = ssl_sect' >> /usr/lib/ssl/openssl.cnf \
      && echo >> /usr/lib/ssl/openssl.cnf \
      && echo -e '[ssl_sect]' >> /usr/lib/ssl/openssl.cnf \
      && echo -e 'system_default = system_default_sect' >> /usr/lib/ssl/openssl.cnf \
      && echo >> /usr/lib/ssl/openssl.cnf \
      && echo -e '[system_default_sect]' >> /usr/lib/ssl/openssl.cnf \
      && echo -e 'MinProtocol = TLSv1.2' >> /usr/lib/ssl/openssl.cnf \
      && echo -e 'CipherString = DEFAULT:@SECLEVEL=1' >> /usr/lib/ssl/openssl.cnf

ENTRYPOINT ["/usr/local/bin/oanda-cli"]
