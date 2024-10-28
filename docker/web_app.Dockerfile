FROM nginx:alpine

COPY web_app/ /usr/share/nginx/html/ 

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
