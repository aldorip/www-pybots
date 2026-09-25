FROM nginx:1.27-alpine

# Timezone America/Sao_Paulo
RUN apk add --no-cache tzdata \
    && cp /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime \
    && echo "America/Sao_Paulo" > /etc/timezone \
    && apk del tzdata

COPY index.html /usr/share/nginx/html/index.html
COPY assets/   /usr/share/nginx/html/assets/

EXPOSE 80
