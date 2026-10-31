/* ============================================================
   PYBOTS — Interações
   Terminal animado, partículas, navegação, formulário e config.
   ============================================================ */
(function () {
  'use strict';

  const config = window.PYBOTS_CONFIG || {};
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Links configuráveis ---------- */
  document.querySelectorAll('[data-config-link]').forEach((el) => {
    const key = el.getAttribute('data-config-link');
    const url = config[key];
    if (url) {
      el.setAttribute('href', url);
    }
  });

  /* ---------- Ano no rodapé ---------- */
  const yearEl = document.getElementById('footerYear');
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  /* ---------- Header: sombra ao rolar + barra de progresso ---------- */
  const header = document.getElementById('siteHeader');
  const progress = document.getElementById('scrollProgress');
  let ticking = false;
  window.addEventListener(
    'scroll',
    () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        const y = window.scrollY;
        header && header.classList.toggle('is-scrolled', y > 8);
        if (progress) {
          const max = document.documentElement.scrollHeight - window.innerHeight;
          progress.style.width = (max > 0 ? (y / max) * 100 : 0) + '%';
        }
        ticking = false;
      });
    },
    { passive: true }
  );

  /* ---------- Menu mobile ---------- */
  const menuToggle = document.getElementById('menuToggle');
  const siteNav = document.getElementById('siteNav');
  if (menuToggle && siteNav) {
    menuToggle.addEventListener('click', () => {
      const open = siteNav.classList.toggle('is-open');
      menuToggle.setAttribute('aria-expanded', String(open));
      menuToggle.setAttribute(
        'aria-label',
        open ? 'Fechar menu de navegação' : 'Abrir menu de navegação'
      );
    });
    siteNav.addEventListener('click', (e) => {
      if (e.target.closest('a')) {
        siteNav.classList.remove('is-open');
        menuToggle.setAttribute('aria-expanded', 'false');
      }
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && siteNav.classList.contains('is-open')) {
        siteNav.classList.remove('is-open');
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.focus();
      }
    });
  }

  /* ---------- Link ativo na navegação ---------- */
  const navLinks = Array.from(document.querySelectorAll('.site-nav a[href^="#"]'));
  const sections = navLinks
    .map((l) => document.querySelector(l.getAttribute('href')))
    .filter(Boolean);

  if ('IntersectionObserver' in window && sections.length) {
    const setActive = (id) => {
      navLinks.forEach((l) =>
        l.classList.toggle('is-active', l.getAttribute('href') === '#' + id)
      );
    };
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActive(entry.target.id);
        });
      },
      { rootMargin: '-40% 0px -55% 0px' }
    );
    sections.forEach((s) => io.observe(s));
  }

  /* ---------- Terminal animado ---------- */
  const terminalBody = document.getElementById('terminalBody');
  if (terminalBody) {
    const LINES = [
      { cls: 't-prompt', text: '$ ' },
      { cls: 't-cmd', text: 'python -m pybots.core\n' },
      { cls: 't-tag', text: '[pybots] ' },
      { cls: 't-cmd', text: 'conectando sistemas........ ' },
      { cls: 't-ok', text: 'OK\n' },
      { cls: 't-tag', text: '[pybots] ' },
      { cls: 't-cmd', text: 'iniciando automação......... ' },
      { cls: 't-ok', text: 'OK\n' },
      { cls: 't-tag', text: '[pybots] ' },
      { cls: 't-cmd', text: 'bots em produção............ ' },
      { cls: 't-ok', text: 'OK\n' },
      { cls: 't-tag', text: '[pybots] ' },
      { cls: 't-cmd', text: 'monitorando tempo real...... ' },
      { cls: 't-ok', text: 'OK\n' },
      { cls: 't-final', text: '→ soluções sob medida, prontas para deploy_' },
    ];

    const renderStatic = () => {
      terminalBody.innerHTML = LINES.map(
        (l) => '<span class="' + l.cls + '">' + l.text.replace(/</g, '<') + '</span>'
      ).join('');
    };

    if (prefersReducedMotion) {
      renderStatic();
    } else {
      let line = 0, char = 0, out = '';
      const caret = '<span class="t-caret"></span>';
      const type = () => {
        if (line >= LINES.length) {
          setTimeout(() => { line = 0; char = 0; out = ''; type(); }, 4200);
          return;
        }
        const l = LINES[line];
        if (char === 0 && l.text.startsWith('$ ')) {
          out += '<span class="t-prompt">$ </span>';
          char = 2;
          setTimeout(type, 350);
          return;
        }
        const piece = l.text.slice(char, char + 1);
        out += '<span class="' + l.cls + '">' + piece.replace(/</g, '<') + '</span>';
        char++;
        terminalBody.innerHTML = out + caret;
        let delay = 14;
        if (piece === '\n') delay = 220;
        if (line === 1 && char > 4) delay = 60;
        if (char >= l.text.length) { line++; char = 0; delay = 90; }
        setTimeout(type, delay);
      };
      type();
    }
  }

  /* ---------- Partículas discretas ---------- */
  const canvas = document.getElementById('particles');
  if (canvas && !prefersReducedMotion) {
    const ctx = canvas.getContext('2d');
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let w = 0, h = 0, particles = [], running = true;
    const mouse = { x: -9999, y: -9999 };

    const resize = () => {
      const rect = canvas.parentElement.getBoundingClientRect();
      w = rect.width; h = rect.height;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.min(Math.floor(w / 18), 70);
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.25,
        r: Math.random() * 1.4 + 0.6,
      }));
    };

    const step = () => {
      if (!running) return;
      ctx.clearRect(0, 0, w, h);
      const LINK = 120;
      for (const p of particles) {
        const dx = p.x - mouse.x, dy = p.y - mouse.y;
        const dist = Math.hypot(dx, dy);
        if (dist < 140 && dist > 0) {
          p.vx += (dx / dist) * 0.02;
          p.vy += (dy / dist) * 0.02;
        }
        p.vx = Math.max(-0.6, Math.min(0.6, p.vx));
        p.vy = Math.max(-0.6, Math.min(0.6, p.vy));
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(88, 166, 255, 0.45)';
        ctx.fill();
      }
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i], b = particles[j];
          const d = Math.hypot(a.x - b.x, a.y - b.y);
          if (d < LINK) {
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = 'rgba(34, 211, 238, ' + (0.12 * (1 - d / LINK)).toFixed(3) + ')';
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(step);
    };

    canvas.parentElement.addEventListener('pointermove', (e) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    });
    canvas.parentElement.addEventListener('pointerleave', () => {
      mouse.x = -9999; mouse.y = -9999;
    });

    if ('IntersectionObserver' in window) {
      new IntersectionObserver((entries) => {
        const visible = entries[0].isIntersecting;
        if (visible && !running) { running = true; step(); }
        else if (!visible) { running = false; }
      }).observe(canvas);
    }
    resize();
    window.addEventListener('resize', resize, { passive: true });
    step();
  }

  /* ---------- Contadores ---------- */
  const counters = document.querySelectorAll('[data-count]');
  if (counters.length && 'IntersectionObserver' in window && !prefersReducedMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        io.unobserve(el);
        const target = parseInt(el.getAttribute('data-count'), 10) || 0;
        const t0 = performance.now(), dur = 900;
        const tick = (t) => {
          const k = Math.min((t - t0) / dur, 1);
          el.textContent = String(Math.round(target * (1 - Math.pow(1 - k, 3))));
          if (k < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      });
    }, { threshold: 0.6 });
    counters.forEach((c) => io.observe(c));
  }

  /* ---------- Formulário de orçamento ---------- */
  const form = document.getElementById('contactForm');
  if (form) {
    const status = document.getElementById('formStatus');
    const showStatus = (msg, ok) => {
      status.textContent = msg;
      status.className = 'form-status is-visible ' + (ok ? 'is-success' : 'is-error');
    };

    const setError = (input, msg) => {
      const err = form.querySelector('[data-error-for="' + input.id + '"]');
      if (msg) {
        input.setAttribute('aria-invalid', 'true');
        if (err) err.textContent = msg;
      } else {
        input.removeAttribute('aria-invalid');
        if (err) err.textContent = '';
      }
    };

    form.addEventListener('submit', (e) => {
      e.preventDefault();

      /* Honeypot: bots preenchem, humanos não veem */
      if (form.website.value.trim() !== '') {
        showStatus('Solicitação registrada. Obrigado!', true);
        return;
      }

      const nome = form.nome.value.trim();
      const email = form.email.value.trim();
      const desc = form.descricao.value.trim();

      let valid = true;
      if (nome.length < 2) { setError(form.nome, 'Informe seu nome.'); valid = false; } else setError(form.nome, '');
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { setError(form.email, 'Informe um e-mail válido.'); valid = false; } else setError(form.email, '');
      if (desc.length < 10) { setError(form.descricao, 'Descreva o projeto com um pouco mais de detalhe.'); valid = false; } else setError(form.descricao, '');

      if (!valid) {
        showStatus('Revise os campos destacados.', false);
        return;
      }

      const tipo = form.tipo.value;
      const empresa = form.empresa.value.trim();
      const whats = form.whatsapp.value.trim();
      const lines = [
        'Solicitação de orçamento — PYBOTS',
        '',
        'Nome: ' + nome,
        empresa ? 'Empresa: ' + empresa : '',
        'E-mail: ' + email,
        whats ? 'WhatsApp: ' + whats : '',
        'Tipo de solução: ' + tipo,
        '',
        'Projeto:',
        desc,
      ].filter(Boolean);

      const btn = document.getElementById('submitBtn');
      btn.disabled = true;
      btn.textContent = 'Enviando…';

      const finish = () => {
        btn.disabled = false;
        btn.textContent = 'Enviar solicitação';
        showStatus(
          'Recebemos sua solicitação. Retornaremos em breve pelo contato informado.',
          true
        );
        form.reset();
      };

      const message = lines.join('\n');
      if (config.whatsappNumber) {
        const url =
          'https://wa.me/' + config.whatsappNumber +
          '?text=' + encodeURIComponent(message);
        window.open(url, '_blank', 'noopener');
        setTimeout(finish, 400);
      } else if (config.email) {
        const url =
          'mailto:' + config.email +
          '?subject=' + encodeURIComponent('Orçamento PYBOTS — ' + tipo) +
          '&body=' + encodeURIComponent(message);
        window.location.href = url;
        setTimeout(finish, 600);
      } else {
        finish();
      }
    });
  }
})();
