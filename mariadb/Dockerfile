FROM mariadb:10.4-bionic AS builder

RUN apt-get update && apt-get install -y \
  git \
  build-essential \
  libmariadbclient-dev \
  libmariadbclient18=1:10.1.44-0ubuntu0.18.04.1 \
  libbsd-dev

RUN mkdir /bcrypt_auth_plugin && git clone --single-branch --branch cleartext https://github.com/Limpan/bcrypt_auth_plugin.git /bcrypt_auth_plugin

RUN (cd /bcrypt_auth_plugin && make)


FROM mariadb:10.4-bionic

RUN apt-get update && apt-get install -y libbsd0 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /bcrypt_auth_plugin/lib/auth_bcrypt.so /usr/lib/x86_64-linux-gnu/mariadb18/plugin/

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
  python3 \
  python3-setuptools \
  python3-pip \
  && rm -rf /var/lib/apt/lists/* \
  && python3 -m pip install --upgrade pip \
  && python3 -m pip install \
      arrow \
      bcrypt \
      click \
      xkcdpass

# Set the locale, ref: http://jaredmarkell.com/docker-and-locales/
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
  locale-gen

COPY mariadb/mariadb.cnf /etc/mysql/conf.d/

COPY user.py /usr/local/bin/user

COPY mariadb/docker-entrypoint.sh /usr/local/bin/
#RUN ln -s /usr/local/bin/docker-entrypoint.sh /

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

ENTRYPOINT [ "docker-entrypoint.sh" ]
CMD [ "mysqld" ]
