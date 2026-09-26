FROM python:3.12-alpine

# Timezone + wget para download do GeoIP
RUN apk add --no-cache tzdata wget \
    && cp /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime \
    && echo "America/Sao_Paulo" > /etc/timezone \
    && apk del tzdata

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x download_geoip.sh

# Volume para SQLite + GeoIP .mmdb
VOLUME ["/data"]

EXPOSE 8000

# Entrypoint: tenta baixar GeoIP, depois sobe o servidor
CMD sh download_geoip.sh && uvicorn main:app --host 0.0.0.0 --port 8000
