# PYBOTS — Portal de Tecnologia, Automação e Desenvolvimento

Site institucional e comercial da **PYBOTS**: desenvolvimento de APIs, bots,
automação de processos, integração de sistemas, IA aplicada e sistemas web sob medida.

## Visão geral

Portal estático de página única, construído para funcionar como máquina de
aquisição de clientes e construção de comunidade:

- **Hero** com terminal animado e partículas discretas
- **Ecossistema** — seis áreas de atuação
- **Projetos** — portfólio real, com links para o GitHub
- **PYBOTS Free** — biblioteca de ferramentas gratuitas da comunidade
- **Serviços sob medida** — proposta comercial e processo de trabalho
- **Comunidade** — CTA para o grupo do Telegram
- **Contato** — formulário de orçamento com validação, honeypot antispam
  e envio via WhatsApp ou e-mail

## Stack

Primeira versão 100% estática — sem backend e sem banco de dados:

| Camada    | Escolha                                            |
|-----------|----------------------------------------------------|
| Frontend  | HTML5 + CSS3 + JavaScript vanilla (sem framework)  |
| Fontes    | Clash Display, Satoshi (Fontshare) + JetBrains Mono |
| Deploy    | Docker/Nginx, Vercel, Netlify ou GitHub Pages      |

> **Evolução recomendada:** quando surgir a área de membros, biblioteca de
> downloads ou painel administrativo, migrar para **Astro + Tailwind**
> (conteúdo em MDX, islands de interatividade) com backend conforme a
> necessidade — a estrutura de pastas já foi organizada pensando nisso.

## Estrutura

```
www-pybots/
├── index.html        # página única com todas as seções
├── base.css          # reset e base de acessibilidade
├── style.css         # design system e componentes
├── app.js            # interações (terminal, partículas, form, nav)
├── config.js         # ⚙️ links e contatos — EDITE AQUI
├── robots.txt
├── sitemap.xml
├── Dockerfile        # deploy em contêiner (Nginx)
├── nginx.conf
└── assets/           # imagens WebP, favicon, OG cover
```

## Configuração

Todos os links externos ficam em **`config.js`** — nenhum outro arquivo
precisa ser alterado para trocar contatos:

```js
window.PYBOTS_CONFIG = {
  telegramGroup: 'https://t.me/...',   // grupo da comunidade
  whatsappNumber: '5585999999999',    // WhatsApp comercial (vazio = envia por e-mail)
  email: 'contato@pybots.com.br',
  github: 'https://github.com/aldorip',
};
```

Enquanto `whatsappNumber` estiver vazio, o formulário de orçamento é
enviado por e-mail (mailto). Ao preencher o número, o envio passa a abrir
o WhatsApp com a mensagem já formatada.

## Rodando localmente

```bash
# qualquer servidor estático
python3 -m http.server 8080
# ou
npx serve .
```

## Deploy

### Docker (VPS / Dokploy)

```bash
docker build -t pybots-site .
docker run -d -p 8080:80 --name pybots-site pybots-site
```

### Alternativas sem servidor

- **Vercel / Netlify:** importar o repositório, sem configuração extra
- **GitHub Pages:** Settings → Pages → branch `main`

## Acessibilidade e performance

- Navegação por teclado, skip link, `aria-*` nos controles
- Respeito a `prefers-reduced-motion` (animações desligadas)
- Contraste WCAG AA em textos
- Revelações no scroll sem deslocamento de layout (sem CLS)
- Imagens WebP com `loading="lazy"` e dimensões explícitas
- Carga inicial ≈ 180 KB

## Roadmap

- [ ] Área de membros da comunidade
- [ ] Biblioteca de downloads (scripts e templates)
- [ ] Login de usuários e painel administrativo
- [ ] Sistema de artigos e tutoriais
- [ ] Migração para Astro + CMS headless

---

**PYBOTS** — Transformamos ideias em soluções inteligentes.
