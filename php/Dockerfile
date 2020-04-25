FROM php:fpm

RUN apt-get update && apt-get install -y --no-install-recommends \
  default-libmysqlclient-dev \
  zlib1g-dev \
  && docker-php-ext-configure pdo_mysql --with-pdo-mysql=/usr --with-zlib-dir=/usr \
  && docker-php-ext-install -j$(nproc) pdo_mysql \
  && rm -rf /var/lib/apt/lists/*

# Use the default production configuration
COPY php/php.ini "$PHP_INI_DIR/php.ini"
