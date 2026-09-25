FROM nginx:1.27-alpine

# Timezone America/Sao_Paulo
RUN apk add --no-cache tzdata \
    && cp /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime \
    && echo "America/Sao_Paulo" > /etc/timezone \
    && apk del tzdata

# Remove o default.conf que pode conflitar
RUN rm /etc/nginx/conf.d/default.conf

# Config mínima
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Arquivos estáticos
COPY index.html /usr/share/nginx/html/index.html
COPY assets/    /usr/share/nginx/html/assets/

EXPOSE 80
