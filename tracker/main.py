"""
PyBots Tracker — FastAPI app
Endpoints:
  POST /t/pv            — pageview
  POST /t/event         — evento genérico (clique, scroll, form, vídeo)
  GET  /t/ranking       — top produtos (público, usado pela landing page)
  GET  /analytics       — dashboard HTML (autenticado)
  GET  /analytics/api/* — dados JSON para o dashboard
"""
import os
import secrets
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import init_db, get_or_create_session, insert_event
from geo import lookup
import queries

# ─────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────
TRACKER_SECRET  = os.getenv("TRACKER_SECRET", "pybots-admin")
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://www.pybots.com.br,http://localhost,http://localhost:8080"
).split(",")

# ─────────────────────────────────────────────
#  Lifespan
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

# ─────────────────────────────────────────────
#  Rate limiter
# ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ─────────────────────────────────────────────
#  App
# ─────────────────────────────────────────────
app = FastAPI(
    title="PyBots Tracker",
    docs_url=None,   # desativa /docs em produção
    redoc_url=None,
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

# ─────────────────────────────────────────────
#  Auth (dashboard)
# ─────────────────────────────────────────────
security = HTTPBasic()

def require_auth(credentials: HTTPBasicCredentials = Depends(security)):
    ok = secrets.compare_digest(
        credentials.password.encode(), TRACKER_SECRET.encode()
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def get_client_ip(request: Request) -> str:
    """Respeita X-Forwarded-For do Traefik."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host or "0.0.0.0"


# ─────────────────────────────────────────────
#  Schemas
# ─────────────────────────────────────────────
class PageviewPayload(BaseModel):
    sid:      str = Field(..., min_length=8, max_length=64)
    url:      Optional[str] = None
    referrer: Optional[str] = None


class EventPayload(BaseModel):
    sid:      str = Field(..., min_length=8, max_length=64)
    type:     str = Field(..., max_length=32)
    category: Optional[str] = Field(None, max_length=64)
    label:    Optional[str] = Field(None, max_length=128)
    url:      Optional[str] = Field(None, max_length=1024)
    value:    Optional[str] = Field(None, max_length=512)


# ─────────────────────────────────────────────
#  Coleta — Pageview
# ─────────────────────────────────────────────
@app.post("/t/pv", status_code=204)
@limiter.limit("60/minute")
async def track_pageview(request: Request, payload: PageviewPayload):
    ip       = get_client_ip(request)
    ua       = request.headers.get("User-Agent", "")
    referrer = payload.referrer or request.headers.get("Referer", "")
    geo      = lookup(ip)

    await get_or_create_session(
        sid=payload.sid,
        ip=ip,
        user_agent=ua,
        referrer=referrer,
        geo=geo,
    )
    await insert_event(
        session_id=payload.sid,
        event_type="pageview",
        url=payload.url,
    )
    return Response(status_code=204)


# ─────────────────────────────────────────────
#  Coleta — Evento genérico
# ─────────────────────────────────────────────
@app.post("/t/event", status_code=204)
@limiter.limit("120/minute")
async def track_event(request: Request, payload: EventPayload):
    ip  = get_client_ip(request)
    ua  = request.headers.get("User-Agent", "")
    geo = lookup(ip)

    # Garante que a sessão existe mesmo se /t/pv não foi chamado
    await get_or_create_session(
        sid=payload.sid,
        ip=ip,
        user_agent=ua,
        referrer="",
        geo=geo,
    )
    await insert_event(
        session_id=payload.sid,
        event_type=payload.type,
        category=payload.category,
        label=payload.label,
        url=payload.url,
        value=payload.value,
    )
    return Response(status_code=204)


# ─────────────────────────────────────────────
#  Público — Ranking de produtos (usado pela landing page)
# ─────────────────────────────────────────────
@app.get("/t/ranking")
async def public_ranking():
    """Top 3 produtos mais clicados — sem autenticação."""
    data = await queries.get_public_ranking(limit=3)
    return JSONResponse(content=data)


# ─────────────────────────────────────────────
#  Dashboard — HTML
# ─────────────────────────────────────────────
@app.get("/analytics", response_class=HTMLResponse)
async def dashboard(_user: str = Depends(require_auth)):
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(dashboard_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ─────────────────────────────────────────────
#  Dashboard — APIs JSON
# ─────────────────────────────────────────────
@app.get("/analytics/api/overview")
async def api_overview(
    period: str = "7d",
    _user: str = Depends(require_auth),
):
    data = await queries.get_overview(period)
    return JSONResponse(content=data)


@app.get("/analytics/api/products")
async def api_products(
    period: str = "7d",
    _user: str = Depends(require_auth),
):
    data = await queries.get_top_products(period=period)
    return JSONResponse(content=data)


@app.get("/analytics/api/countries")
async def api_countries(
    period: str = "7d",
    _user: str = Depends(require_auth),
):
    data = await queries.get_top_countries(period=period)
    return JSONResponse(content=data)


@app.get("/analytics/api/timeline")
async def api_timeline(
    days: int = 30,
    _user: str = Depends(require_auth),
):
    data = await queries.get_visitors_by_day(days=days)
    return JSONResponse(content=data)


@app.get("/analytics/api/funnel")
async def api_funnel(
    period: str = "30d",
    _user: str = Depends(require_auth),
):
    data = await queries.get_contact_funnel(period=period)
    return JSONResponse(content=data)


@app.get("/analytics/api/videos")
async def api_videos(
    period: str = "7d",
    _user: str = Depends(require_auth),
):
    data = await queries.get_video_views(period=period)
    return JSONResponse(content=data)


@app.get("/analytics/api/events")
async def api_events(
    page: int = 1,
    category: Optional[str] = None,
    period: str = "7d",
    _user: str = Depends(require_auth),
):
    data = await queries.get_events_table(page=page, category=category, period=period)
    return JSONResponse(content=data)


@app.get("/analytics/api/referrers")
async def api_referrers(
    period: str = "7d",
    _user: str = Depends(require_auth),
):
    data = await queries.get_top_referrers(period=period)
    return JSONResponse(content=data)


@app.get("/analytics/api/devices")
async def api_devices(
    period: str = "7d",
    _user: str = Depends(require_auth),
):
    data = await queries.get_device_split(period=period)
    return JSONResponse(content=data)


# ─────────────────────────────────────────────
#  Health
# ─────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}
