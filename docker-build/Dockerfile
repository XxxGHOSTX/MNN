FROM nginx:1.25.3-bookworm

LABEL org.opencontainers.image.created=1970-01-01T00:00:00Z

ARG SOURCE_DATE_EPOCH=0
ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}

RUN apt-get update && \
    apt-get install -y --no-install-recommends php8.2-fpm=8.2.28-1~deb12u1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
