# Design — Analytics & Rastreamento PyBots

## Arquitetura Geral

```
┌─────────────────────────────────────────────────────┐
│                  www.pybots.com.br                  │
│                                                     │
│  index.html                                         │
│  └── assets/tracker.js  ──────────────────────────┐ │
│       (async, non-blocking)                       │ │
└───────────────────────────────────────────────────┼─┘
                                                    │
                    HTTP POST (beacon)              │
                                                    ▼
┌─────────────────────────────────────────────────────┐
│           tracker-api  (FastAPI / Python)           │
│                                                     │
│  POST /t/event          ← coleta de eventos         │
│  POST /t/pv             ← coleta de pageview        │
│  GET  /analytics        ← dashboard (auth)          │
│  GET  /analytics/api/*  ← dados JSON para charts    │
│                                                     │
│  ┌──────────────┐    ┌─────────────────────────┐   │
│  │  GeoIP2 DB   │    │     SQLite (events.db)  │   │
│  │ (GeoLite2)   │    │                         │   │
│  └──────────────┘    └─────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Estrutura de Arquivos

```
www-pybots/
├── index.html
├── assets/
│   ├── style.css
│   ├── main.js
│   └── tracker.js          ← NOVO: script de rastreamento
│
├── tracker/                ← NOVO: serviço de analytics
│   ├── main.py             ← FastAPI app
│   ├── database.py         ← SQLite + models
│   ├── geo.py              ← GeoIP2 lookup
│   ├── dashboard.html      ← painel admin
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml      ← atualizado com serviço tracker
├── Dockerfile              ← landing page (nginx)
└── nginx.conf
```

## Banco de Dados (SQLite)

### Tabela: `sessions`
```sql
CREATE TABLE sessions (
    id          TEXT PRIMARY KEY,        -- UUID
    ip_hash     TEXT NOT NULL,           -- SHA-256(ip + salt)
    ip_raw      TEXT,                    -- IP original (opcional, pode omitir por LGPD)
    country     TEXT,
    city        TEXT,
    region      TEXT,
    isp         TEXT,
    user_agent  TEXT,
    device      TEXT,                    -- "mobile" | "desktop" | "tablet"
    referrer    TEXT,
    created_at  DATETIME DEFAULT (datetime('now','localtime')),
    last_seen   DATETIME
);
```

### Tabela: `events`
```sql
CREATE TABLE events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT REFERENCES sessions(id),
    type        TEXT NOT NULL,           -- "pageview" | "click" | "scroll" | "form"
    category    TEXT,                    -- "produto" | "contato" | "nav" | "formulario"
    label       TEXT,                    -- "bot-blaze" | "whatsapp" | etc
    url         TEXT,
    value       TEXT,                    -- dado extra (ex: % scroll, serviço do form)
    created_at  DATETIME DEFAULT (datetime('now','localtime'))
);
```

## tracker.js — Lógica do Frontend

```javascript
// Fluxo:
// 1. Ao carregar → gera/recupera session_id do cookie
// 2. Envia pageview imediatamente (sendBeacon)
// 3. Intercepta cliques em [data-track] via event delegation
// 4. Monitora scroll depth (25/50/75/100%)
// 5. Monitora tempo na página (30s, 60s, 120s)
// 6. Busca ranking de produtos em /t/ranking e aplica destaques
// 7. Inicializa modais de vídeo nos cards que tiverem data-video

// Atributos HTML para rastrear:
// <a data-track="produto" data-label="bot-blaze" href="...">
// <button data-track="contato" data-label="whatsapp">

// Atributos para vídeo:
// <div class="product-card" data-video="https://youtube.com/embed/ID" data-product-id="bot-blaze">
```

## Destaque Dinâmico nos Cards

### Endpoint público (sem auth)
```
GET /t/ranking
Response: { "top": ["bot-blaze", "syspdv", "whatticket"], "counts": {...} }
```

### CSS — Classes de destaque aplicadas via JS
```css
/* Top 1 — Mais popular */
.product-card.rank-1 {
  border-color: #f59e0b;
  box-shadow: 0 0 0 1px #f59e0b,
              0 0 30px rgba(245,158,11,0.25),
              0 0 60px rgba(245,158,11,0.1);
  transform: scale(1.03);
  animation: rankGlow 3s ease-in-out infinite;
}
.product-card.rank-1 .rank-badge { display: flex; } /* "🔥 Mais popular" */

/* Top 2 e 3 — Em alta */
.product-card.rank-2,
.product-card.rank-3 {
  border-color: rgba(121,131,245,0.5);
}
.product-card.rank-2 .rank-badge,
.product-card.rank-3 .rank-badge { display: flex; } /* "⭐ Em alta" */

@keyframes rankGlow {
  0%, 100% { box-shadow: 0 0 20px rgba(245,158,11,0.2); }
  50%       { box-shadow: 0 0 40px rgba(245,158,11,0.4); }
}
```

### Lógica JS em tracker.js
```javascript
async function applyRanking() {
  const res = await fetch('/t/ranking');
  const { top } = await res.json();
  top.forEach((productId, i) => {
    const card = document.querySelector(`[data-product-id="${productId}"]`);
    if (card) card.classList.add(`rank-${i + 1}`);
  });
}
// Executar no load e re-executar a cada 30 minutos
applyRanking();
setInterval(applyRanking, 30 * 60 * 1000);
```

## Modal de Vídeo

### HTML injetado dinamicamente
```html
<div id="video-modal" class="video-modal hidden">
  <div class="video-backdrop"></div>
  <div class="video-container">
    <button class="video-close">✕</button>
    <iframe id="video-frame" src="" allowfullscreen></iframe>
  </div>
</div>
```

### CSS do Modal
```css
.video-modal { position:fixed; inset:0; z-index:200; display:flex; align-items:center; justify-content:center }
.video-backdrop { position:absolute; inset:0; background:rgba(0,0,0,0.85); backdrop-filter:blur(8px) }
.video-container { position:relative; z-index:1; width:min(860px,95vw); aspect-ratio:16/9; border-radius:16px; overflow:hidden }
.video-close { position:absolute; top:-40px; right:0; background:none; border:none; color:#fff; font-size:1.5rem; cursor:pointer }
```



```
POST /t/event
Content-Type: application/json

{
  "sid": "uuid-session",
  "type": "click",
  "category": "produto",
  "label": "bot-blaze",
  "url": "https://t.me/seubot",
  "ts": 1727301600000
}
```

Resposta: `204 No Content` (rápido, sem body)

## Dashboard — Telas

### Visão Geral (`/analytics`)
- Cards: Visitantes hoje / 7d / 30d — Sessões — Cliques totais
- Gráfico de linha: visitantes por dia (últimos 30 dias)
- Top 5 produtos clicados (barras horizontais)
- Top países (lista com bandeiras)
- Split mobile vs desktop (donut)

### Funil de Contato — seção destacada no dashboard
```
Visitantes totais
      ↓
Viram a seção de contato       (visibilidade / secao-contato)
      ↓
Leram por +3 segundos          (engajamento / contato-lido)
      ↓
Iniciaram o formulário         (formulario / iniciou)
      ↓
Clicaram no WhatsApp           (contato / whatsapp)
      ↓
Enviaram o formulário          (formulario / submit)
```
Exibido como funil visual com % de conversão em cada etapa.
Responde à pergunta: **"De cada 100 visitantes, quantos chegaram a querer contato?"**

### Tabela de Eventos (`/analytics/events`)
- Filtro por: período, categoria, label, país
- Colunas: data/hora, cidade, país, dispositivo, evento, label
- Paginação 50 por página

### Mapa de Interesse (`/analytics/produtos`)
- Ranking completo de todos os labels clicados
- Gráfico de funil: visualizações → cliques → WhatsApp

## docker-compose.yml — Atualização

```yaml
services:
  www-pybots:
    # ... existente

  tracker:
    build: ./tracker
    container_name: pybots-tracker
    restart: unless-stopped
    environment:
      TZ: America/Sao_Paulo
      TRACKER_SECRET: ${TRACKER_SECRET}   # senha do dashboard
      GEOIP_PATH: /data/GeoLite2-City.mmdb
    volumes:
      - tracker-data:/data
    networks:
      - dokploy-network

volumes:
  tracker-data:
```

## Segurança

- Endpoint `/t/*` → rate limit 60 req/min por IP (slowapi)
- Dashboard `/analytics` → HTTP Basic Auth com `TRACKER_SECRET`
- IPs hasheados: `SHA256(ip + SECRET_SALT)` — não reversível
- CORS: aceita apenas origem `https://www.pybots.com.br`

## Stack Técnica

| Componente | Tecnologia |
|---|---|
| Coleta frontend | JavaScript vanilla (tracker.js) |
| API coleta | FastAPI + Python 3.12 |
| Banco | SQLite via aiosqlite |
| Geolocalização | MaxMind GeoLite2 (offline) |
| Dashboard UI | HTML + Chart.js (sem framework) |
| Rate limiting | slowapi |
| Container | Python 3.12-alpine |
