# Requirements — Analytics & Rastreamento PyBots

## Visão Geral

Sistema de rastreamento de visitantes e cliques para a landing page www.pybots.com.br,
com foco em mapear interesse por produto/serviço, origem geográfica e comportamento
de navegação, sem depender de ferramentas de terceiros pagas.

---

## Requisitos Funcionais

### RF-01 — Rastreamento de Pageview

WHEN um visitante acessa qualquer página do site
THE SYSTEM SHALL registrar: IP, timestamp, user-agent, referrer, URL acessada, país, cidade e ISP

WHEN o IP do visitante é recebido
THE SYSTEM SHALL realizar geolocalização via banco GeoIP2 (MaxMind GeoLite2) localmente

### RF-02 — Rastreamento de Cliques em Links de Produto

WHEN um visitante clica em qualquer botão de produto ou CTA da landing page
THE SYSTEM SHALL registrar: produto clicado, timestamp, session_id do visitante, URL destino

WHEN o visitante clica em "Solicitar licença" do Bot Blaze
THE SYSTEM SHALL registrar o evento com categoria="produto" e label="bot-blaze"

WHEN o visitante clica em "Solicitar demonstração" do WhatTicket
THE SYSTEM SHALL registrar o evento com categoria="produto" e label="whatticket"

WHEN o visitante clica em "Solicitar demonstração" do SysPDV
THE SYSTEM SHALL registrar o evento com categoria="produto" e label="syspdv"

WHEN o visitante clica em "Saber mais" do LLM Gateway
THE SYSTEM SHALL registrar o evento com categoria="produto" e label="llm-gateway"

WHEN o visitante clica em "Ver documentação" da API Cassino
THE SYSTEM SHALL registrar o evento com categoria="produto" e label="api-cassino"

WHEN o visitante clica em "Saber mais" do Ollama Gateway
THE SYSTEM SHALL registrar o evento com categoria="produto" e label="ollama-gateway"

### RF-03 — Rastreamento de Visualização e Cliques em Contato

WHEN o visitante rola a página e a seção #contato entra na viewport
THE SYSTEM SHALL registrar evento com categoria="visibilidade" e label="secao-contato"
  — isso indica intenção: o visitante chegou até o contato

WHEN o visitante mantém a seção #contato visível por mais de 3 segundos
THE SYSTEM SHALL registrar evento com categoria="engajamento" e label="contato-lido"
  — diferencia quem "passou rolando" de quem "leu de verdade"

WHEN o visitante clica no link de WhatsApp
THE SYSTEM SHALL registrar evento com categoria="contato" e label="whatsapp"

WHEN o visitante clica no link de e-mail
THE SYSTEM SHALL registrar evento com categoria="contato" e label="email"

WHEN o visitante clica no link do GitHub
THE SYSTEM SHALL registrar evento com categoria="contato" e label="github"

WHEN o visitante submete o formulário de contato
THE SYSTEM SHALL registrar evento com categoria="formulario" e label="submit" e o serviço selecionado

WHEN o visitante começa a preencher o formulário (foca em qualquer campo)
THE SYSTEM SHALL registrar evento com categoria="formulario" e label="iniciou"
  — captura quem começou mas não terminou (abandono de formulário)

### RF-04 — Rastreamento de Scroll e Engajamento

WHEN o visitante rola a página e atinge 25%, 50%, 75% ou 100% do conteúdo
THE SYSTEM SHALL registrar evento de scroll_depth com o percentual correspondente

WHEN o visitante permanece na página por mais de 30 segundos
THE SYSTEM SHALL registrar evento time_on_page com o tempo acumulado

### RF-05 — Destaque Dinâmico por Popularidade

WHEN a landing page carrega
THE SYSTEM SHALL consultar o endpoint `/t/ranking` e receber os top produtos por cliques/visualizações

WHEN um produto está no top 1 do ranking
THE SYSTEM SHALL aplicar no card correspondente:
  - Badge "🔥 Mais popular" visível
  - Borda com efeito glow animado na cor do produto
  - Leve escala aumentada (transform: scale) para se destacar dos demais

WHEN um produto está no top 2 ou top 3 do ranking
THE SYSTEM SHALL aplicar badge "⭐ Em alta" com destaque menor

WHEN não há dados suficientes (menos de 10 eventos registrados)
THE SYSTEM SHALL exibir os cards normalmente sem destaque

WHEN o ranking muda ao longo do tempo
THE SYSTEM SHALL atualizar o destaque a cada 30 minutos via re-fetch silencioso

### RF-06 — Suporte a Vídeos nos Cards de Produto

WHEN um card de produto possui um vídeo configurado
THE SYSTEM SHALL exibir um botão "▶ Ver demonstração" abaixo da descrição

WHEN o visitante clica em "▶ Ver demonstração"
THE SYSTEM SHALL abrir um modal/lightbox com o vídeo incorporado (YouTube, Vimeo ou arquivo .mp4)

WHEN o modal de vídeo abre
THE SYSTEM SHALL registrar evento com categoria="video" e label=<nome-do-produto>

WHEN o visitante fecha o modal
THE SYSTEM SHALL pausar o vídeo automaticamente

WHEN o vídeo não está configurado para um produto
THE SYSTEM SHALL ocultar o botão de vídeo sem afetar o layout

### RF-07 — Dashboard de Analytics

WHEN o administrador acessa /analytics com credenciais válidas
THE SYSTEM SHALL exibir painel com:
  - Total de visitantes únicos (hoje, 7 dias, 30 dias)
  - Mapa de calor por país/cidade
  - Ranking de produtos mais clicados
  - Fontes de tráfego (referrer)
  - Dispositivos (mobile/desktop)
  - Tabela de visitantes recentes com IP, localização, cliques

WHEN o administrador filtra por período
THE SYSTEM SHALL atualizar todos os gráficos e tabelas em tempo real

### RF-06 — Identificação de Sessão

WHEN um visitante acessa o site pela primeira vez
THE SYSTEM SHALL gerar um session_id único (UUID) armazenado em cookie por 30 minutos

WHEN o mesmo visitante retorna em menos de 30 minutos
THE SYSTEM SHALL associar os eventos ao mesmo session_id (sessão existente)

WHEN o visitante retorna após 30 minutos ou em nova aba privada
THE SYSTEM SHALL criar um novo session_id

---

## Requisitos Não Funcionais

### RNF-01 — Performance
- O script de tracking NÃO deve bloquear o carregamento da página (async)
- Cada evento deve ser enviado via `navigator.sendBeacon()` ou fetch não bloqueante
- O endpoint de coleta deve responder em menos de 50ms

### RNF-02 — Privacidade
- Nenhum dado deve ser enviado a terceiros
- IPs devem ser armazenados hasheados (SHA-256 + salt) para LGPD
- O sistema deve funcionar mesmo com bloqueadores de anúncios (endpoint próprio, não `/analytics`)

### RNF-03 — Persistência
- Dados armazenados em SQLite (suficiente para o volume esperado)
- Backup automático diário via cron

### RNF-04 — Segurança
- Dashboard protegido por autenticação HTTP Basic ou token
- Endpoint de coleta protegido contra spam com rate limiting (max 60 req/min por IP)

---

## Casos de Uso Estratégicos

1. **Identificar qual produto gera mais interesse** → priorizar marketing e desenvolvimento
2. **Mapear de onde vêm os visitantes** → definir onde anunciar (cidade, região)
3. **Saber qual canal traz mais tráfego** → medir ROI de posts no Telegram, WhatsApp etc.
4. **Funil de contato completo:**
   - Quantos chegaram até a seção de contato (viram)
   - Quantos leram por mais de 3 segundos (intenção real)
   - Quantos começaram a preencher o formulário (iniciaram)
   - Quantos clicaram no WhatsApp (ação direta)
   - Quantos enviaram o formulário (conversão)
   → Identificar onde as pessoas desistem e otimizar
5. **Ver quem clicou em WhatsApp mas não converteu** → criar estratégia de follow-up
6. **Identificar horários de pico** → programar posts e atualizações no melhor horário
7. **Abandono de formulário** → quem começou a preencher mas não enviou é um lead quente perdido
