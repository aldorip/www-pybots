"""
PyBots Tracker — Geolocalização offline via MaxMind GeoLite2
"""
import os
import logging

logger = logging.getLogger(__name__)

GEOIP_PATH = os.getenv("GEOIP_PATH", "/data/GeoLite2-City.mmdb")

_reader = None


def _get_reader():
    """Carrega o reader GeoIP2 uma única vez (singleton)."""
    global _reader
    if _reader is not None:
        return _reader
    try:
        import geoip2.database
        if os.path.exists(GEOIP_PATH):
            _reader = geoip2.database.Reader(GEOIP_PATH)
            logger.info(f"GeoIP2 carregado: {GEOIP_PATH}")
        else:
            logger.warning(f"GeoIP2 não encontrado em {GEOIP_PATH} — geolocalização desativada")
    except Exception as e:
        logger.error(f"Erro ao carregar GeoIP2: {e}")
    return _reader


def lookup(ip: str) -> dict:
    """
    Retorna dados de geolocalização para o IP.
    Fallback gracioso: retorna campos vazios se GeoIP não estiver disponível.
    """
    empty = {"country": None, "city": None, "region": None, "isp": None}

    if not ip or ip in ("127.0.0.1", "::1"):
        return {**empty, "country": "Local"}

    reader = _get_reader()
    if reader is None:
        return empty

    try:
        response = reader.city(ip)
        return {
            "country": response.country.name or None,
            "city":    response.city.name or None,
            "region":  response.subdivisions.most_specific.name or None,
            "isp":     None,  # GeoLite2-City não inclui ISP (requer ASN db)
        }
    except Exception:
        # IP não encontrado na base ou formato inválido
        return empty


def lookup_country_iso(ip: str) -> str | None:
    """Retorna apenas o código ISO do país (ex: 'BR')."""
    reader = _get_reader()
    if reader is None:
        return None
    try:
        return reader.city(ip).country.iso_code
    except Exception:
        return None
