# Tasks — Analytics & Rastreamento PyBots

## Fase 1 — Backend (API de Coleta)

- [ ] 1. Criar estrutura do serviço `tracker/`
  - Criar pasta `tracker/` na raiz do projeto
  - Criar `tracker/requirements.txt` com: fastapi, uvicorn, aiosqlite, geoip2, slowapi, python-multipart
  - Criar `tracker/Dockerfile` baseado em python:3.12-alpine

- [ ] 2. Banco de dados SQLite
  - Criar `tracker/database.py` com:
    - Função `init_db()` criando tabelas `sessions` e `events`
    - Função `get_or_create_session(sid, dados_geo, user_agent, referrer)`
    - Função `insert_event(session_id, type, category, label, url, value)`
    - Função `update_session_last_seen(sid)`

- [ ] 3. Geolocalização
  - Criar `tracker/geo.py` com:
    - Função `lookup(ip)` → retorna `{country, city, region, isp}`
    - Download automático do GeoLite2-City.mmdb se não existir
    - Fallback gracioso se GeoIP falhar (retorna campos vazios)

- [ ] 4. Endpoints de coleta (FastAPI)
  - Criar `tracker/main.py` com:
    - `POST /t/pv` — pageview (cria/atualiza sessão + insere evento)
    - `POST /t/event` — evento genérico (clique, scroll, form)
    - Rate limiting: 60 req/min por IP via slowapi
    - CORS liberado apenas para `www.pybots.com.br`
    - Hashing do IP: `SHA256(ip + SALT)` antes de armazenar
    - Resposta sempre `204 No Content`

## Fase 2 — Frontend (tracker.js)

- [ ] 5. Criar `assets/tracker.js`
  - Gerenciamento de sessão:
    - Gerar UUID v4 se não existir cookie `_pbsid`
    - Salvar cookie com `max-age=1800` (30 min), `SameSite=Lax`
  - Envio de pageview no load (via `sendBeacon` ou `fetch` keep-alive)
  - Event delegation para cliques em `[data-track]`:
    - Captura `data-track` (categoria) e `data-label`
    - Envia evento assíncrono sem bloquear navegação

- [ ] 6. Adicionar atributos `data-track` e `data-product-id` no `index.html`
  - Todos os botões de produto nos cards:
    - `data-track="produto" data-label="bot-blaze"` + `data-product-id="bot-blaze"` no card pai
    - `data-track="produto" data-label="whatticket"` + `data-product-id="whatticket"`
    - `data-track="produto" data-label="syspdv"` + `data-product-id="syspdv"`
    - `data-track="produto" data-label="llm-gateway"` + `data-product-id="llm-gateway"`
    - `data-track="produto" data-label="api-cassino"` + `data-product-id="api-cassino"`
    - `data-track="produto" data-label="ollama-gateway"` + `data-product-id="ollama-gateway"`
  - Links de contato:
    - `data-track="contato" data-label="whatsapp"`
    - `data-track="contato" data-label="email"`
    - `data-track="contato" data-label="github"`
  - Links de serviços na navbar:
    - `data-track="nav" data-label="servicos"` etc
  - Adicionar `rank-badge` oculto em cada card:
    ```html
    <div class="rank-badge" style="display:none">🔥 Mais popular</div>
    ```

- [ ] 7. Rastreamento de scroll depth no `tracker.js`
  - Usar `IntersectionObserver` nas seções para detectar 25/50/75/100%
  - Disparar evento `scroll` uma única vez por threshold por sessão

- [ ] 8. Rastreamento de tempo na página
  - Cronômetro iniciado no load
  - Enviar eventos nos marcos: 30s, 60s, 120s, 300s
  - Usar `visibilitychange` para pausar quando aba está em background

- [ ] 9. Rastreamento do formulário de contato e visibilidade da seção
  - Interceptar scroll até `#contato` via `IntersectionObserver`
    - Disparar evento `categoria="visibilidade" label="secao-contato"` ao entrar na viewport
    - Iniciar timer: se ficar visível por +3s → `categoria="engajamento" label="contato-lido"`
  - Interceptar foco em qualquer campo do `#contactForm`
    - Disparar evento `categoria="formulario" label="iniciou"` (uma única vez por sessão)
  - Interceptar submit do `#contactForm`
    - Capturar campo `service` selecionado
    - Enviar evento `categoria="formulario" label="submit" value=<service>`

- [ ] 10. Destaque dinâmico por ranking em `tracker.js`
  - Função `applyRanking()`:
    - Fetch em `GET /t/ranking`
    - Para o top 1: adicionar classe `rank-1` ao card + mostrar badge "🔥 Mais popular"
    - Para top 2 e 3: adicionar classe `rank-2`/`rank-3` + badge "⭐ Em alta"
    - Remover classes anteriores antes de reaplicar
  - Executar no load da página
  - Re-executar a cada 30 minutos silenciosamente
  - Adicionar CSS das classes `rank-1/2/3` em `style.css`:
    - `rank-1`: borda âmbar + glow animado + `scale(1.03)`
    - `rank-2/3`: borda roxa sutil

- [ ] 11. Modal de vídeo em `tracker.js` + `index.html`
  - Injetar HTML do modal no `body` via JS (uma vez no load)
  - Para cada card com `data-video="URL"`:
    - Adicionar botão "▶ Ver demonstração" dinamicamente
    - Ao clicar: abrir modal, setar `src` do iframe, registrar evento `categoria="video"`
  - Fechar modal: botão ✕, clique no backdrop, tecla Escape
  - Ao fechar: limpar `src` do iframe para pausar o vídeo
  - Adicionar CSS do modal em `style.css`

## Fase 3 — Dashboard

- [ ] 12. Queries de analytics em `tracker/queries.py`
  - `get_visitors_count(period)` → total visitantes únicos
  - `get_top_products(limit=10)` → ranking de produtos clicados
  - `get_top_countries(limit=10)` → visitantes por país
  - `get_referrers(limit=10)` → top fontes de tráfego
  - `get_device_split()` → % mobile vs desktop
  - `get_events_table(page, filters)` → tabela paginada
  - `get_visitors_by_day(days=30)` → série temporal
  - `get_contact_funnel()` → funil completo:
    - total sessões → viram contato → leram 3s → iniciaram form → clicaram WhatsApp → enviaram form
    - % de conversão entre cada etapa
  - `get_public_ranking(limit=3)` → top produtos para `/t/ranking` (landing page)
  - `get_video_views()` → produtos com mais plays de vídeo

- [ ] 13. Endpoints em `tracker/main.py`
  - `GET /t/ranking` → JSON público top 3 produtos (sem auth, usado pela landing page)
  - `GET /analytics` → serve `dashboard.html` (auth required)
  - `GET /analytics/api/overview` → cards de resumo
  - `GET /analytics/api/products` → ranking produtos
  - `GET /analytics/api/countries` → países
  - `GET /analytics/api/timeline` → série temporal
  - `GET /analytics/api/funnel` → funil de contato
  - `GET /analytics/api/videos` → plays de vídeo por produto
  - `GET /analytics/api/events` → tabela paginada

- [ ] 14. Criar `tracker/dashboard.html`
  - Layout dark (consistente com a landing page)
  - Cards de resumo: visitantes hoje / 7d / 30d
  - Gráfico de linha (Chart.js): visitantes por dia
  - **Funil de contato visual** — barras decrescentes com % em cada etapa
  - Barras horizontais: top produtos — destaque especial para o #1
  - Plays de vídeo por produto
  - Lista: top países com bandeiras emoji
  - Donut: mobile vs desktop
  - Tabela de eventos recentes com filtros por categoria/período
  - Auto-refresh a cada 60 segundos

## Fase 4 — Infraestrutura

- [ ] 15. Atualizar `docker-compose.yml`
  - Adicionar serviço `tracker` com build `./tracker`
  - Volume `tracker-data` para persistir SQLite e GeoIP DB
  - Variável de ambiente `TRACKER_SECRET`
  - Expor rotas `/analytics` e `/t/*` via Dokploy/Traefik

- [ ] 16. Incluir `tracker.js` no `index.html`
  - Adicionar `<script src="/assets/tracker.js" defer></script>` antes do `</body>`

- [ ] 17. Configurar download do GeoLite2
  - Script `tracker/download_geoip.sh`
  - Documentar como obter license key gratuita da MaxMind

## Fase 5 — Testes e Validação

- [ ] 18. Testar coleta localmente
  - Subir `docker compose up`, clicar em todos os botões de produto
  - Verificar SQLite: eventos registrados, ranking retornado corretamente
  - Verificar destaque visual aplicado no card correto

- [ ] 19. Testar vídeos
  - Adicionar `data-video` de teste em um card
  - Verificar abertura do modal, rastreamento do evento e fechamento

- [ ] 20. Testar dashboard
  - Funil de contato com dados reais
  - Ranking refletindo os cliques do teste
  - Gráficos carregando corretamente

- [ ] 21. Deploy no Dokploy
  - Push de todos os arquivos
  - Configurar `TRACKER_SECRET` no painel
  - Configurar domínio `analytics.pybots.com.br` ou `/analytics`

## Ordem de Execução

```
1 → 2 → 3 → 4        (backend funcional)
        ↓
5 → 6 → 9 → 10       (tracking + destaque por ranking)
        ↓
    11 (modal vídeo)
        ↓
12 → 13 → 14          (dashboard com funil)
        ↓
15 → 16 → 17          (infra)
        ↓
18 → 19 → 20 → 21     (testes + deploy)
```
