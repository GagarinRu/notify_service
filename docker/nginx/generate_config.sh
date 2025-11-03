#!/bin/sh
set -e

envsubst '${NGINX_BACKEND_HOST} ${NGINX_BACKEND_PORT} ${NGINX_PORT}' \
  < /etc/site.conf \
  > /etc/nginx/conf.d/default.conf

rm /etc/nginx/conf.d/site.conf
rm /etc/nginx/site.conf
rm /etc/nginx/site.conf.template

exec nginx -g 'daemon off;'