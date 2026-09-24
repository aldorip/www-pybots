# www-pybots

Landing page oficial da **PyBots** — sua central de automação, bots, WhatsApp, PDV, APIs e sistemas.

## Visão Geral

Este repositório contém o site institucional da PyBots, projetado para:

- Apresentar todos os produtos e sistemas desenvolvidos
- Exibir portfólio de clientes ativos e cases de sucesso
- Facilitar contato para novos projetos e contratos
- Servir como hub central para links de sistemas em produção

## Stack Recomendada

Para uma landing page moderna, rápida e fácil de manter, inspirada em sites como GitHub, Discord e Stripe:

- **Framework:** [Astro](https://astro.build/) (SSG focado em performance e SEO)
- **UI:** [Tailwind CSS](https://tailwindcss.com/) + componentes reutilizáveis
- **Deploy:** Vercel, Netlify ou Cloudflare Pages (gratuito e com CDN global)
- **CMS (opcional):** Decap CMS ou Sanity para conteúdo dinâmico

## Estrutura do Projeto

```
www-pybots/
├── public/              # Assets estáticos (imagens, favicon, etc.)
├── src/
│   ├── components/      # Componentes UI (Header, Footer, Cards, etc.)
│   ├── layouts/         # Layouts base (MainLayout.astro)
│   ├── pages/           # Páginas (index.astro, about.astro, contact.astro)
│   └── styles/          # Estilos globais
├── astro.config.mjs     # Configuração do Astro
├── tailwind.config.mjs  # Configuração do Tailwind
└── package.json         # Dependências
```

## Próximos Passos

1. Configurar ambiente Astro + Tailwind
2. Criar estrutura de páginas e componentes
3. Adicionar conteúdo sobre produtos PyBots
4. Integrar formulário de contato (ex: Formspree ou EmailJS)
5. Deploy automático via GitHub Actions

## Links Úteis

- [Documentação Astro](https://docs.astro.build/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Exemplos de landing pages](https://github.com/topics/landing-page-template)

---

**PyBots** — Automatizando o futuro, um bot de cada vez.
