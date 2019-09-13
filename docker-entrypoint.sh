#!/bin/sh
set -e

# Environment variables that are used if not empty:
#   SERVER_NAMES
#   USERNAME
#   PASSWORD

# Just in case this environment variable has gone missing.
HTTPD_PREFIX="${HTTPD_PREFIX:-/usr/local/apache2}"

# Configure vhosts.
if [ "x$SERVER_NAMES" != "x" ]; then
    # Use first domain as Apache ServerName.
    SERVER_NAME="${SERVER_NAMES%%,*}"
    sed -e "s|ServerName .*|ServerName $SERVER_NAME|" \
        -i "$HTTPD_PREFIX"/conf/sites-available/default.conf

    # Replace commas with spaces and set as Apache ServerAlias.
    SERVER_ALIAS="`printf '%s\n' "$SERVER_NAMES" | tr ',' ' '`"
    sed -e "/ServerName/a\ \ ServerAlias $SERVER_ALIAS" \
        -i "$HTTPD_PREFIX"/conf/sites-available/default.conf
fi

# Add password hash, unless "user.passwd" already exists (ie, bind mounted).
if [ ! -e "/user.passwd" ]; then
    user passwd > /user.passwd
fi

[ ! -d "/var/www/html" ] && mkdir -p "/var/www/html"
chown -R www-data:www-data "/var/www/html"

# Create directories for Dav data and lock database.
[ ! -d "/var/lib/dav/data" ] && mkdir -p "/var/lib/dav/data"
[ ! -e "/var/lib/dav/DavLock" ] && touch "/var/lib/dav/DavLock"
chown -R www-data:www-data "/var/lib/dav"

exec "$@"
