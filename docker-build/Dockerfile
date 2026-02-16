FROM nginx:1.25.3
MAINTAINER XxxGHOSTX maintainer@example.com
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get install -y php-fpm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
