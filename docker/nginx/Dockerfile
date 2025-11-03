FROM nginx:alpine

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/configs/site.conf /etc/site.conf
COPY docker/nginx/generate_config.sh /generate_config.sh

RUN chmod +x /generate_config.sh

CMD ["/generate_config.sh"]