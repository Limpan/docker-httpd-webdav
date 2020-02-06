FROM httpd:2.4.37-alpine

# These variables are inherited from the httpd:alpine image:
# ENV HTTPD_PREFIX /usr/local/apache2
# WORKDIR "$HTTPD_PREFIX"

# Copy in our configuration files.
COPY conf/ conf/

RUN set -ex; \
    # Install build dependencies
    apk add --no-cache --virtual .build-deps \
        build-base \
        python3-dev \
        libffi-dev; \
    \
    # Install Python and PIP
    apk add --no-cache --update \
        python3 \
        py3-setuptools; \
    \
    # Upgrade PIP
    pip3 install --upgrade pip; \
    \
    # Install Python packages
    pip install \
        arrow \
        bcrypt \
        click \
        xkcdpass; \
    \
    # Remove dependencies
    apk del .build-deps; \
    \
    # Enable FCGI
    for i in proxy proxy_fcgi; do \
        sed -i -e "/^#LoadModule ${i}_module.*/s/^#//" "conf/httpd.conf"; \
    done; \
    \
    # Create empty default DocumentRoot.
    mkdir -p "/var/www/html"; \
    # Create directories for Dav data and lock database.
    mkdir -p "/var/lib/dav/data"; \
    touch "/var/lib/dav/DavLock"; \
    chown -R www-data:www-data "/var/lib/dav"; \
    \
    # Enable DAV modules.
    for i in dav dav_fs dav_lock; do \
        sed -i -e "/^#LoadModule ${i}_module.*/s/^#//" "conf/httpd.conf"; \
    done; \
    \
    # Make sure authentication modules are enabled.
    for i in authn_core authn_file authz_core authz_user auth_basic; do \
        sed -i -e "/^#LoadModule ${i}_module.*/s/^#//" "conf/httpd.conf"; \
    done; \
    \
    # Make sure other modules are enabled.
    for i in alias headers mime setenvif rewrite; do \
        sed -i -e "/^#LoadModule ${i}_module.*/s/^#//" "conf/httpd.conf"; \
    done; \
    \
    # Run httpd as "www-data" (instead of "daemon").
    for i in User Group; do \
        sed -i -e "s|^$i .*|$i www-data|" "conf/httpd.conf"; \
    done; \
    \
    # Include enabled configs and sites.
    printf '%s\n' "Include conf/conf-enabled/*.conf" \
        >> "conf/httpd.conf"; \
    printf '%s\n' "Include conf/sites-enabled/*.conf" \
        >> "conf/httpd.conf"; \
    \
    # Enable dav and default site.
    mkdir -p "conf/conf-enabled"; \
    mkdir -p "conf/sites-enabled"; \
    ln -s ../conf-available/dav.conf "conf/conf-enabled"; \
    ln -s ../conf-available/git.conf "conf/conf-enabled"; \
    ln -s ../sites-available/default.conf "conf/sites-enabled";

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY user.py /usr/local/bin/user

EXPOSE 80/tcp
ENTRYPOINT [ "docker-entrypoint.sh" ]
CMD [ "httpd-foreground" ]
