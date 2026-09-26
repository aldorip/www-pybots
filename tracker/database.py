"""
PyBots Tracker — Database layer (aiosqlite + SQLite)
"""
import hashlib
import os
import aiosqlite

DB_PATH = os.getenv("DB_PATH", "/data/events.db")
SALT = os.getenv("TRACKER_SALT", "pybots-default-salt-change-me")


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def hash_ip(ip: str) -> str:
    """SHA-256(ip + salt) — não reversível, compatível LGPD."""
    return hashlib.sha256(f"{ip}{SALT}".encode()).hexdigest()


def detect_device(user_agent: str) -> str:
    ua = (user_agent or "").lower()
    if any(k in ua for k in ("iphone", "android", "mobile", "phone")):
        return "mobile"
    if any(k in ua for k in ("ipad", "tablet")):
        return "tablet"
    return "desktop"


# ─────────────────────────────────────────────
#  Init
# ─────────────────────────────────────────────

async def init_db() -> None:
    """Cria as tabelas se não existirem."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          TEXT PRIMARY KEY,
                ip_hash     TEXT NOT NULL,
                country     TEXT,
                city        TEXT,
                region      TEXT,
                isp         TEXT,
                user_agent  TEXT,
                device      TEXT,
                referrer    TEXT,
                created_at  TEXT DEFAULT (datetime('now','localtime')),
                last_seen   TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT REFERENCES sessions(id),
                type        TEXT NOT NULL,
                category    TEXT,
                label       TEXT,
                url         TEXT,
                value       TEXT,
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE INDEX IF NOT EXISTS idx_events_session   ON events(session_id);
            CREATE INDEX IF NOT EXISTS idx_events_type      ON events(type);
            CREATE INDEX IF NOT EXISTS idx_events_category  ON events(category);
            CREATE INDEX IF NOT EXISTS idx_events_label     ON events(label);
            CREATE INDEX IF NOT EXISTS idx_events_created   ON events(created_at);
            CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);
        """)
        await db.commit()


# ─────────────────────────────────────────────
#  Sessions
# ─────────────────────────────────────────────

async def get_or_create_session(
    sid: str,
    ip: str,
    user_agent: str,
    referrer: str,
    geo: dict,
) -> str:
    """Retorna o session_id (cria se não existir, atualiza last_seen se existir)."""
    ip_hash = hash_ip(ip)
    device = detect_device(user_agent)

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM sessions WHERE id = ?", (sid,)
        ) as cur:
            row = await cur.fetchone()

        if row:
            await db.execute(
                "UPDATE sessions SET last_seen = datetime('now','localtime') WHERE id = ?",
                (sid,),
            )
        else:
            await db.execute(
                """INSERT INTO sessions
                   (id, ip_hash, country, city, region, isp, user_agent, device, referrer)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    sid,
                    ip_hash,
                    geo.get("country"),
                    geo.get("city"),
                    geo.get("region"),
                    geo.get("isp"),
                    user_agent[:512] if user_agent else None,
                    device,
                    referrer[:512] if referrer else None,
                ),
            )
        await db.commit()
    return sid


# ─────────────────────────────────────────────
#  Events
# ─────────────────────────────────────────────

async def insert_event(
    session_id: str,
    event_type: str,
    category: str | None = None,
    label: str | None = None,
    url: str | None = None,
    value: str | None = None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO events (session_id, type, category, label, url, value)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, event_type, category, label,
             url[:1024] if url else None,
             value[:512] if value else None),
        )
        await db.commit()
