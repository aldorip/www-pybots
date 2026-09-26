#!/bin/sh
# ──────────────────────────────────────────────────────
# Download do MaxMind GeoLite2-City.mmdb
# Necessário: variável MAXMIND_LICENSE_KEY no ambiente
#
# Obtenha sua chave gratuita em:
# https://www.maxmind.com/en/geolite2/signup
# ──────────────────────────────────────────────────────

set -e

DEST="/data/GeoLite2-City.mmdb"
KEY="${MAXMIND_LICENSE_KEY}"

if [ -z "$KEY" ]; then
  echo "[geoip] MAXMIND_LICENSE_KEY não definida — pulando download"
  exit 0
fi

if [ -f "$DEST" ]; then
  echo "[geoip] GeoLite2-City.mmdb já existe em $DEST"
  exit 0
fi

echo "[geoip] Baixando GeoLite2-City.mmdb..."
URL="https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${KEY}&suffix=tar.gz"

cd /tmp
wget -q -O geoip.tar.gz "$URL"
tar -xzf geoip.tar.gz
find . -name "GeoLite2-City.mmdb" -exec mv {} "$DEST" \;
rm -rf geoip.tar.gz GeoLite2-City_*

echo "[geoip] Download concluído: $DEST"
