"""
PyBots Tracker — Queries de analytics
"""
import aiosqlite
from database import DB_PATH

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

PERIOD_MAP = {
    "1d":  "datetime('now','localtime','-1 day')",
    "7d":  "datetime('now','localtime','-7 days')",
    "30d": "datetime('now','localtime','-30 days')",
    "all": "datetime('2000-01-01')",
}

def period_filter(period: str) -> str:
    return PERIOD_MAP.get(period, PERIOD_MAP["7d"])


async def fetchall(sql: str, params: tuple = ()) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, params) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def fetchone(sql: str, params: tuple = ()) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, params) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


# ─────────────────────────────────────────────
#  Overview — cards do dashboard
# ─────────────────────────────────────────────

async def get_overview(period: str = "7d") -> dict:
    since = period_filter(period)

    visitors = await fetchone(
        f"SELECT COUNT(DISTINCT id) as total FROM sessions WHERE created_at >= {since}"
    )
    sessions = await fetchone(
        f"SELECT COUNT(*) as total FROM sessions WHERE created_at >= {since}"
    )
    clicks = await fetchone(
        f"""SELECT COUNT(*) as total FROM events
            WHERE category = 'produto' AND created_at >= {since}"""
    )
    contacts = await fetchone(
        f"""SELECT COUNT(DISTINCT session_id) as total FROM events
            WHERE category = 'contato' AND created_at >= {since}"""
    )
    # Período anterior para comparativo
    prev_map = {"1d": "-2 days", "7d": "-14 days", "30d": "-60 days", "all": "-9999 days"}
    prev_since = f"datetime('now','localtime','{prev_map.get(period,'-14 days')}')"
    prev_visitors = await fetchone(
        f"""SELECT COUNT(DISTINCT id) as total FROM sessions
            WHERE created_at >= {prev_since} AND created_at < {since}"""
    )

    def pct_change(curr, prev):
        if not prev or prev == 0:
            return None
        return round(((curr - prev) / prev) * 100, 1)

    v_curr = visitors["total"] if visitors else 0
    v_prev = prev_visitors["total"] if prev_visitors else 0

    return {
        "visitors":      v_curr,
        "visitors_pct":  pct_change(v_curr, v_prev),
        "sessions":      sessions["total"] if sessions else 0,
        "product_clicks": clicks["total"] if clicks else 0,
        "contacts":      contacts["total"] if contacts else 0,
    }


# ─────────────────────────────────────────────
#  Produtos
# ─────────────────────────────────────────────

async def get_top_products(period: str = "7d", limit: int = 10) -> list[dict]:
    since = period_filter(period)
    return await fetchall(
        f"""SELECT label, COUNT(*) as clicks
            FROM events
            WHERE category = 'produto' AND label IS NOT NULL AND created_at >= {since}
            GROUP BY label
            ORDER BY clicks DESC
            LIMIT ?""",
        (limit,),
    )


async def get_public_ranking(limit: int = 3) -> dict:
    """Endpoint público usado pela landing page para destaques."""
    rows = await get_top_products(period="30d", limit=limit)
    top   = [r["label"] for r in rows]
    counts = {r["label"]: r["clicks"] for r in rows}
    return {"top": top, "counts": counts}


# ─────────────────────────────────────────────
#  Países e cidades
# ─────────────────────────────────────────────

async def get_top_countries(period: str = "7d", limit: int = 10) -> list[dict]:
    since = period_filter(period)
    return await fetchall(
        f"""SELECT country, COUNT(*) as visitors
            FROM sessions
            WHERE country IS NOT NULL AND created_at >= {since}
            GROUP BY country
            ORDER BY visitors DESC
            LIMIT ?""",
        (limit,),
    )


async def get_top_cities(period: str = "7d", country: str = "Brazil", limit: int = 10) -> list[dict]:
    since = period_filter(period)
    return await fetchall(
        f"""SELECT city, region, COUNT(*) as visitors
            FROM sessions
            WHERE country = ? AND city IS NOT NULL AND created_at >= {since}
            GROUP BY city
            ORDER BY visitors DESC
            LIMIT ?""",
        (country, limit),
    )


# ─────────────────────────────────────────────
#  Referrers (fontes de tráfego)
# ─────────────────────────────────────────────

async def get_top_referrers(period: str = "7d", limit: int = 10) -> list[dict]:
    since = period_filter(period)
    return await fetchall(
        f"""SELECT
              CASE
                WHEN referrer IS NULL OR referrer = '' THEN 'Direto'
                WHEN referrer LIKE '%t.me%' OR referrer LIKE '%telegram%' THEN 'Telegram'
                WHEN referrer LIKE '%google%' THEN 'Google'
                WHEN referrer LIKE '%whatsapp%' OR referrer LIKE '%wa.me%' THEN 'WhatsApp'
                WHEN referrer LIKE '%github%' THEN 'GitHub'
                WHEN referrer LIKE '%instagram%' THEN 'Instagram'
                WHEN referrer LIKE '%facebook%' THEN 'Facebook'
                ELSE referrer
              END as source,
              COUNT(*) as visitors
            FROM sessions
            WHERE created_at >= {since}
            GROUP BY source
            ORDER BY visitors DESC
            LIMIT ?""",
        (limit,),
    )


# ─────────────────────────────────────────────
#  Dispositivos
# ─────────────────────────────────────────────

async def get_device_split(period: str = "7d") -> list[dict]:
    since = period_filter(period)
    return await fetchall(
        f"""SELECT device, COUNT(*) as total
            FROM sessions
            WHERE created_at >= {since}
            GROUP BY device
            ORDER BY total DESC""",
    )


# ─────────────────────────────────────────────
#  Série temporal
# ─────────────────────────────────────────────

async def get_visitors_by_day(days: int = 30) -> list[dict]:
    return await fetchall(
        """SELECT
             strftime('%Y-%m-%d', created_at) as day,
             COUNT(DISTINCT id) as visitors
           FROM sessions
           WHERE created_at >= datetime('now','localtime', ? || ' days')
           GROUP BY day
           ORDER BY day ASC""",
        (f"-{days}",),
    )


# ─────────────────────────────────────────────
#  Funil de contato
# ─────────────────────────────────────────────

async def get_contact_funnel(period: str = "30d") -> list[dict]:
    since = period_filter(period)

    async def count_sessions_with_event(category: str, label: str | None = None) -> int:
        if label:
            row = await fetchone(
                f"""SELECT COUNT(DISTINCT session_id) as total FROM events
                    WHERE category = ? AND label = ? AND created_at >= {since}""",
                (category, label),
            )
        else:
            row = await fetchone(
                f"""SELECT COUNT(DISTINCT session_id) as total FROM events
                    WHERE category = ? AND created_at >= {since}""",
                (category,),
            )
        return row["total"] if row else 0

    total_visitors = (await fetchone(
        f"SELECT COUNT(DISTINCT id) as total FROM sessions WHERE created_at >= {since}"
    ) or {}).get("total", 0)

    saw_contact    = await count_sessions_with_event("visibilidade", "secao-contato")
    read_contact   = await count_sessions_with_event("engajamento",  "contato-lido")
    started_form   = await count_sessions_with_event("formulario",   "iniciou")
    clicked_wa     = await count_sessions_with_event("contato",      "whatsapp")
    submitted_form = await count_sessions_with_event("formulario",   "submit")

    def pct(part, total):
        if not total:
            return 0.0
        return round((part / total) * 100, 1)

    return [
        {"step": "Visitantes totais",       "count": total_visitors, "pct": 100.0},
        {"step": "Viram seção contato",      "count": saw_contact,    "pct": pct(saw_contact,    total_visitors)},
        {"step": "Leram por +3s",            "count": read_contact,   "pct": pct(read_contact,   total_visitors)},
        {"step": "Iniciaram formulário",     "count": started_form,   "pct": pct(started_form,   total_visitors)},
        {"step": "Clicaram no WhatsApp",     "count": clicked_wa,     "pct": pct(clicked_wa,     total_visitors)},
        {"step": "Enviaram formulário",      "count": submitted_form, "pct": pct(submitted_form, total_visitors)},
    ]


# ─────────────────────────────────────────────
#  Vídeos
# ─────────────────────────────────────────────

async def get_video_views(period: str = "7d", limit: int = 10) -> list[dict]:
    since = period_filter(period)
    return await fetchall(
        f"""SELECT label, COUNT(*) as plays
            FROM events
            WHERE category = 'video' AND created_at >= {since}
            GROUP BY label
            ORDER BY plays DESC
            LIMIT ?""",
        (limit,),
    )


# ─────────────────────────────────────────────
#  Tabela de eventos recentes
# ─────────────────────────────────────────────

async def get_events_table(
    page: int = 1,
    category: str | None = None,
    period: str = "7d",
    page_size: int = 50,
) -> dict:
    since = period_filter(period)
    offset = (page - 1) * page_size

    where_cat = "AND e.category = :category" if category else ""
    params = {
        "since": since,
        "limit": page_size,
        "offset": offset,
    }
    if category:
        params["category"] = category

    # SQLite não aceita parâmetros em expressões como datetime(...), usamos f-string só no since
    rows = await fetchall(
        f"""SELECT
              e.created_at,
              s.city, s.country, s.device,
              e.type, e.category, e.label, e.value, e.url,
              s.referrer
            FROM events e
            JOIN sessions s ON s.id = e.session_id
            WHERE e.created_at >= {since}
            {where_cat}
            ORDER BY e.created_at DESC
            LIMIT ? OFFSET ?""",
        (page_size, offset) if not category else (category, page_size, offset),
    )

    total = await fetchone(
        f"""SELECT COUNT(*) as total FROM events e
            WHERE e.created_at >= {since} {where_cat}""",
        () if not category else (category,),
    )

    return {
        "rows":     rows,
        "total":    total["total"] if total else 0,
        "page":     page,
        "page_size": page_size,
    }
