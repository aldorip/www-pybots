/* ============================================================
   PyBots — tracker.js
   Rastreamento de visitantes, cliques, scroll, tempo,
   destaque dinâmico por ranking e modal de vídeo.
   Carrega de forma assíncrona — não bloqueia a página.
   ============================================================ */

(function () {
  'use strict';

  const TRACKER_BASE = '/t';  // ajuste se o tracker estiver em subdomínio

  // ──────────────────────────────────────────
  //  1. Sessão (cookie _pbsid, 30 min)
  // ──────────────────────────────────────────
  function uuidv4() {
    return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
  }

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : null;
  }

  function setCookie(name, value, maxAgeSeconds) {
    document.cookie = `${name}=${encodeURIComponent(value)}; max-age=${maxAgeSeconds}; path=/; SameSite=Lax`;
  }

  function getSessionId() {
    let sid = getCookie('_pbsid');
    if (!sid) {
      sid = uuidv4();
      setCookie('_pbsid', sid, 1800); // 30 minutos
    } else {
      // Renova o cookie a cada interação
      setCookie('_pbsid', sid, 1800);
    }
    return sid;
  }

  const SID = getSessionId();

  // ──────────────────────────────────────────
  //  2. Envio de eventos (sendBeacon ou fetch)
  // ──────────────────────────────────────────
  function send(endpoint, payload) {
    const url  = TRACKER_BASE + endpoint;
    const body = JSON.stringify({ sid: SID, ...payload });
    const blob = new Blob([body], { type: 'application/json' });

    // sendBeacon garante envio mesmo ao navegar para outra página
    if (navigator.sendBeacon && navigator.sendBeacon(url, blob)) return;

    // Fallback: fetch não bloqueante
    fetch(url, {
      method:      'POST',
      body:        body,
      headers:     { 'Content-Type': 'application/json' },
      keepalive:   true,
    }).catch(() => {});
  }

  // ──────────────────────────────────────────
  //  3. Pageview
  // ──────────────────────────────────────────
  send('/pv', {
    url:      location.href,
    referrer: document.referrer || '',
  });

  // ──────────────────────────────────────────
  //  4. Event delegation — cliques em [data-track]
  // ──────────────────────────────────────────
  document.addEventListener('click', function (e) {
    const el = e.target.closest('[data-track]');
    if (!el) return;
    send('/event', {
      type:     'click',
      category: el.dataset.track,
      label:    el.dataset.label  || null,
      url:      el.href           || el.dataset.href || null,
      value:    el.dataset.value  || null,
    });
  }, true);

  // ──────────────────────────────────────────
  //  5. Scroll depth (25 / 50 / 75 / 100%)
  // ──────────────────────────────────────────
  const scrollFired = new Set();

  function checkScrollDepth() {
    const scrolled  = window.scrollY + window.innerHeight;
    const total     = document.documentElement.scrollHeight;
    const pct       = Math.floor((scrolled / total) * 100);
    const marks     = [25, 50, 75, 100];

    marks.forEach(mark => {
      if (pct >= mark && !scrollFired.has(mark)) {
        scrollFired.add(mark);
        send('/event', {
          type:     'scroll',
          category: 'scroll',
          label:    'scroll_depth',
          value:    String(mark),
        });
      }
    });
  }

  window.addEventListener('scroll', checkScrollDepth, { passive: true });

  // ──────────────────────────────────────────
  //  6. Tempo na página (30s / 60s / 120s / 300s)
  // ──────────────────────────────────────────
  const timeFired = new Set();
  let   elapsed   = 0;
  let   timer     = null;

  function tick() { elapsed++; }

  function startTimer()  { if (!timer) timer = setInterval(tick, 1000); }
  function pauseTimer()  { clearInterval(timer); timer = null; }

  document.addEventListener('visibilitychange', () => {
    document.hidden ? pauseTimer() : startTimer();
  });
  startTimer();

  setInterval(() => {
    const marks = [30, 60, 120, 300];
    marks.forEach(mark => {
      if (elapsed >= mark && !timeFired.has(mark)) {
        timeFired.add(mark);
        send('/event', {
          type:     'time',
          category: 'engajamento',
          label:    'time_on_page',
          value:    String(mark),
        });
      }
    });
  }, 5000);

  // ──────────────────────────────────────────
  //  7. Visibilidade da seção #contato
  // ──────────────────────────────────────────
  const contactSection = document.getElementById('contato');

  if (contactSection) {
    let contactVisible    = false;
    let contactViewFired  = false;
    let contactReadFired  = false;
    let contactReadTimer  = null;

    const contactObs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        contactVisible = entry.isIntersecting;

        if (entry.isIntersecting && !contactViewFired) {
          contactViewFired = true;
          send('/event', {
            type:     'visibility',
            category: 'visibilidade',
            label:    'secao-contato',
          });
        }

        if (entry.isIntersecting && !contactReadFired) {
          contactReadTimer = setTimeout(() => {
            if (contactVisible && !contactReadFired) {
              contactReadFired = true;
              send('/event', {
                type:     'engagement',
                category: 'engajamento',
                label:    'contato-lido',
              });
            }
          }, 3000);
        } else {
          clearTimeout(contactReadTimer);
        }
      });
    }, { threshold: 0.4 });

    contactObs.observe(contactSection);
  }

  // ──────────────────────────────────────────
  //  8. Formulário de contato
  // ──────────────────────────────────────────
  const contactForm = document.getElementById('contactForm');

  if (contactForm) {
    let formStartFired = false;

    // Quem começou a preencher
    contactForm.addEventListener('focusin', () => {
      if (!formStartFired) {
        formStartFired = true;
        send('/event', {
          type:     'form',
          category: 'formulario',
          label:    'iniciou',
        });
      }
    }, { once: true });

    // Quem enviou (substituindo o listener do main.js)
    contactForm.addEventListener('submit', () => {
      const service = contactForm.querySelector('#service');
      send('/event', {
        type:     'form',
        category: 'formulario',
        label:    'submit',
        value:    service ? service.value : null,
      });
    });
  }

  // ──────────────────────────────────────────
  //  9. Destaque dinâmico por ranking
  // ──────────────────────────────────────────
  const RANK_LABELS = {
    1: { cls: 'rank-1', text: '🔥 Mais popular' },
    2: { cls: 'rank-2', text: '⭐ Em alta'      },
    3: { cls: 'rank-3', text: '⭐ Em alta'      },
  };

  function clearRanks() {
    document.querySelectorAll('.product-card').forEach(card => {
      card.classList.remove('rank-1', 'rank-2', 'rank-3');
      const badge = card.querySelector('.rank-badge');
      if (badge) { badge.textContent = ''; badge.style.display = 'none'; }
    });
  }

  async function applyRanking() {
    try {
      const res  = await fetch(TRACKER_BASE + '/ranking');
      if (!res.ok) return;
      const data = await res.json();
      const top  = data.top || [];

      clearRanks();

      top.forEach((productId, i) => {
        const rank = i + 1;
        const card = document.querySelector(`[data-product-id="${productId}"]`);
        if (!card || rank > 3) return;

        const { cls, text } = RANK_LABELS[rank];
        card.classList.add(cls);

        let badge = card.querySelector('.rank-badge');
        if (!badge) {
          badge = document.createElement('div');
          badge.className = 'rank-badge';
          card.insertBefore(badge, card.firstChild);
        }
        badge.textContent    = text;
        badge.style.display  = 'inline-flex';
      });
    } catch (_) {
      // falha silenciosa — não afeta a página
    }
  }

  // Aplica no load e a cada 30 minutos
  applyRanking();
  setInterval(applyRanking, 30 * 60 * 1000);

  // ──────────────────────────────────────────
  //  10. Modal de vídeo
  // ──────────────────────────────────────────

  // Injeta HTML do modal uma única vez
  const modalHTML = `
    <div id="pb-video-modal" style="display:none;position:fixed;inset:0;z-index:300;align-items:center;justify-content:center">
      <div id="pb-video-backdrop" style="position:absolute;inset:0;background:rgba(0,0,0,0.88);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)"></div>
      <div style="position:relative;z-index:1;width:min(860px,95vw)">
        <button id="pb-video-close" style="position:absolute;top:-40px;right:0;background:none;border:none;color:#fff;font-size:1.5rem;cursor:pointer;font-family:inherit">✕ fechar</button>
        <div style="position:relative;padding-bottom:56.25%;border-radius:14px;overflow:hidden;background:#000">
          <iframe id="pb-video-frame" src="" allowfullscreen allow="autoplay; encrypted-media"
            style="position:absolute;inset:0;width:100%;height:100%;border:none"></iframe>
        </div>
      </div>
    </div>`;

  document.body.insertAdjacentHTML('beforeend', modalHTML);

  const videoModal   = document.getElementById('pb-video-modal');
  const videoFrame   = document.getElementById('pb-video-frame');
  const videoClose   = document.getElementById('pb-video-close');
  const videoBackdrop = document.getElementById('pb-video-backdrop');

  function openVideo(url, productId) {
    videoFrame.src        = url;
    videoModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    send('/event', {
      type:     'video',
      category: 'video',
      label:    productId || 'unknown',
    });
  }

  function closeVideo() {
    videoFrame.src        = '';   // pausa o vídeo
    videoModal.style.display = 'none';
    document.body.style.overflow = '';
  }

  videoClose.addEventListener('click',   closeVideo);
  videoBackdrop.addEventListener('click', closeVideo);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeVideo();
  });

  // Adiciona botão "▶ Ver demonstração" em cards com data-video
  document.querySelectorAll('.product-card[data-video]').forEach(card => {
    const videoUrl   = card.dataset.video;
    const productId  = card.dataset.productId || '';
    if (!videoUrl) return;

    const btn = document.createElement('button');
    btn.className   = 'btn-video-demo';
    btn.innerHTML   = '▶ Ver demonstração';
    btn.style.cssText = `
      display:inline-flex;align-items:center;gap:6px;
      margin-top:4px;font-size:.82rem;font-weight:600;
      color:#ef4444;background:rgba(239,68,68,.1);
      border:1px solid rgba(239,68,68,.25);border-radius:8px;
      padding:7px 14px;cursor:pointer;font-family:inherit;
      transition:background .2s,color .2s;
    `;
    btn.addEventListener('mouseenter', () => {
      btn.style.background = 'rgba(239,68,68,.2)';
    });
    btn.addEventListener('mouseleave', () => {
      btn.style.background = 'rgba(239,68,68,.1)';
    });
    btn.addEventListener('click', () => openVideo(videoUrl, productId));

    // Insere antes do btn-product
    const btnProduct = card.querySelector('.btn-product');
    if (btnProduct) card.insertBefore(btn, btnProduct);
    else card.appendChild(btn);
  });

})();
