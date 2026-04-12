<div align="center">

# 🏠 ARPILF — Website

**Associação de Reformados, Pensionistas e Idosos**

Site estático · [Hugo](https://gohugo.io/) · [Tailwind CSS](https://tailwindcss.com/) · Deploy automático via GitHub Actions

[![Build & Deploy](https://github.com/BoiDareia/Arpilf/actions/workflows/deploy.yml/badge.svg)](https://github.com/BoiDareia/Arpilf/actions/workflows/deploy.yml)

[🌐 Ver o site](https://arpilf.pt) · [📝 Painel CMS](https://arpilf.pt/admin/) · [📖 Documentação](docs/)

</div>

---

## ⚡ Visão Geral

|               |                                                       |
| ------------- | ----------------------------------------------------- |
| **Framework** | Hugo (extended) — gerador de sites estáticos          |
| **Estilos**   | Tailwind CSS v4 (CLI standalone)                      |
| **CMS**       | Decap CMS — painel web para edição de conteúdos       |
| **Hosting**   | cPanel (online.pt) via FTP                            |
| **CI/CD**     | GitHub Actions — build, validação, Lighthouse, deploy |
| **Domínio**   | [arpilf.pt](https://arpilf.pt)                        |

---

## 📋 Pré-requisitos

| Ferramenta                                                               | Obrigatório | Notas                                     |
| ------------------------------------------------------------------------ | :---------: | ----------------------------------------- |
| [Hugo](https://gohugo.io/installation/) (extended)                       |     ✅      | Versão mais recente                       |
| [Tailwind CSS CLI](https://github.com/tailwindlabs/tailwindcss/releases) |     ✅      | Binário standalone, sem Node.js           |
| [Git](https://git-scm.com/)                                              |     ✅      |                                           |
| [Node.js](https://nodejs.org/)                                           |     ⬜      | Apenas para testes JavaScript             |
| [PHP 8+](https://www.php.net/)                                           |     ⬜      | Apenas para testar formulário de contacto |
| [Python 3.10+](https://www.python.org/)                                  |     ⬜      | Apenas para testes de build               |

---

## 🚀 Setup Local

### 1. Clonar o repositório

```bash
git clone https://github.com/BoiDareia/Arpilf.git
cd Arpilf
```

### 2. Instalar o Tailwind CSS CLI

Descarregar o binário para a raiz do projeto:

<details>
<summary>🐧 Linux</summary>

```bash
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
chmod +x tailwindcss-linux-x64
mv tailwindcss-linux-x64 tailwindcss
```

</details>

<details>
<summary>🍎 macOS (Apple Silicon)</summary>

```bash
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
chmod +x tailwindcss-macos-arm64
mv tailwindcss-macos-arm64 tailwindcss
```

</details>

<details>
<summary>🍎 macOS (Intel)</summary>

```bash
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-x64
chmod +x tailwindcss-macos-x64
mv tailwindcss-macos-x64 tailwindcss
```

</details>

<details>
<summary>🪟 Windows</summary>

Descarregar `tailwindcss-windows-x64.exe` dos [releases](https://github.com/tailwindlabs/tailwindcss/releases) e renomear para `tailwindcss.exe` na raiz do projeto.

</details>

### 3. Compilar CSS + iniciar Hugo

```bash
# Terminal 1 — Tailwind em modo watch
./tailwindcss -i assets/css/main.css -o static/css/style.css --watch

# Terminal 2 — Hugo dev server
hugo server
```

O site fica disponível em `http://localhost:1313/` com live reload.

---

## 🛠️ Comandos

| Comando                                                                 | Descrição                                   |
| ----------------------------------------------------------------------- | ------------------------------------------- |
| `hugo server`                                                           | Servidor de desenvolvimento com live reload |
| `hugo --minify`                                                         | Build de produção → `public/`               |
| `./tailwindcss -i assets/css/main.css -o static/css/style.css --watch`  | Tailwind em modo watch                      |
| `./tailwindcss -i assets/css/main.css -o static/css/style.css --minify` | Tailwind minificado (produção)              |

---

## 📁 Estrutura do Projeto

```text
Arpilf/
├── 📄 hugo.toml                     # Configuração Hugo
├── 📄 tailwind.config.js            # Configuração Tailwind CSS
├── 📄 lighthouserc.json             # Configuração Lighthouse CI
│
├── 📂 .github/workflows/
│   └── deploy.yml                   # Pipeline CI/CD
│
├── 📂 assets/css/
│   └── main.css                     # Tailwind directives (input)
│
├── 📂 content/                      # 📝 Conteúdo Markdown
│   ├── _index.md                    #    Homepage
│   ├── sobre/                       #    Sobre Nós
│   ├── servicos/                    #    Serviços
│   ├── noticias/                    #    Notícias (artigos)
│   ├── documentos/                  #    Documentos
│   ├── contactos/                   #    Contactos
│   ├── donativos/                   #    Donativos
│   ├── parceiros/                   #    Parceiros
│   ├── projectos/                   #    Projectos
│   └── protecao-dados/              #    Política RGPD
│
├── 📂 data/
│   ├── documentos.yaml              # Catálogo de documentos (PDFs)
│   └── projectos.yaml               # Lista de projectos
│
├── 📂 layouts/                      # 🎨 Templates Hugo
│   ├── _default/                    #    Base (baseof, single, list)
│   ├── partials/                    #    Partials (head, nav, footer)
│   └── [secção]/                    #    Templates por secção
│
├── 📂 static/                       # 📦 Ficheiros estáticos
│   ├── admin/                       #    Decap CMS (painel de gestão)
│   ├── oauth/                       #    OAuth provider (autenticação)
│   ├── css/style.css                #    CSS compilado
│   ├── js/                          #    JavaScript
│   ├── images/                      #    Imagens e favicons
│   ├── documentos/                  #    PDFs por categoria
│   ├── contact.php                  #    Handler do formulário
│   └── .htaccess                    #    Redirects, CSP, cache
│
├── 📂 tests/                        # 🧪 Testes
│   ├── build/                       #    Python (pytest/Hypothesis)
│   ├── js/                          #    JavaScript (Vitest/fast-check)
│   └── php/                         #    PHP (PHPUnit/Eris)
│
├── 📂 docs/                         # 📖 Documentação operacional
└── 📂 public/                       # ⚙️ Output do build (não versionar)
```

---

## 📝 Gestão de Conteúdos (CMS)

O website inclui um painel de gestão de conteúdos acessível em **[arpilf.pt/admin/](https://arpilf.pt/admin/)**, baseado no [Decap CMS](https://decapcms.org/).

### O que se pode fazer

| Secção         | Ações                                            |
| -------------- | ------------------------------------------------ |
| **Notícias**   | Criar, editar e apagar artigos de notícias       |
| **Documentos** | Adicionar/remover PDFs organizados por categoria |
| **Projectos**  | Gerir a lista de projectos da associação         |
| **Páginas**    | Editar descrições das páginas principais         |

### Como funciona

```text
Utilizador edita conteúdo no CMS (browser)
  → Decap CMS faz commit no GitHub (branch main)
  → GitHub Actions executa o pipeline automaticamente
  → Site é reconstruído e publicado em poucos minutos
```

### Autenticação

O CMS usa autenticação via GitHub com um OAuth provider self-hosted (PHP) alojado no próprio cPanel. As credenciais OAuth são injetadas automaticamente durante o deploy via GitHub Secrets.

---

## 🔄 CI/CD — Deploy Automático

O deploy é acionado automaticamente a cada push para `main`.

### Pipeline

```text
Push para main
  → Checkout do código
  → Instalar Hugo + Tailwind CSS CLI
  → Compilar CSS (minificado)
  → Build Hugo (minificado)
  → Injetar credenciais OAuth no PHP
  → Validar HTML
  → Lighthouse CI (performance, acessibilidade, SEO)
  → Deploy via FTP para o cPanel
```

> Se qualquer passo falhar, o deploy **não acontece** e o site mantém a versão anterior.

### GitHub Secrets

Configurar em **Settings → Secrets and variables → Actions**:

| Secret                | Descrição                                  |
| --------------------- | ------------------------------------------ |
| `SFTP_HOST`           | Hostname do servidor (ex: `ftp.arpilf.pt`) |
| `SFTP_USER`           | Utilizador FTP do cPanel                   |
| `SFTP_PASSWORD`       | Password FTP do cPanel                     |
| `SFTP_PATH`           | Caminho remoto (ex: `public_html/`)        |
| `OAUTH_CLIENT_ID`     | Client ID da GitHub OAuth App              |
| `OAUTH_CLIENT_SECRET` | Client Secret da GitHub OAuth App          |

### Deploy Manual (alternativa)

<details>
<summary>Instruções para deploy manual</summary>

```bash
# 1. Compilar Tailwind CSS
./tailwindcss -i assets/css/main.css -o static/css/style.css --minify

# 2. Build Hugo
hugo --minify

# 3. Upload via lftp
lftp -e "
  set ssl:verify-certificate no;
  set ftp:ssl-allow yes;
  mirror --reverse --delete --verbose --parallel=4 \
    ./public/ public_html/;
  bye
" -u UTILIZADOR,PASSWORD ftp://HOSTNAME
```

Ou copiar manualmente o conteúdo de `public/` para `public_html/` via FileZilla ou o gestor de ficheiros do cPanel.

</details>

---

## 🧪 Testes

```bash
# JavaScript (chatbot, formulário)
npm install
npm run test:js

# Python (build Hugo, redirects)
pip install pytest hypothesis beautifulsoup4 lxml pyyaml
pytest tests/build/

# PHP (handler do formulário)
cd tests/php && phpunit
```

---

## 🔒 Segurança

O site implementa os seguintes cabeçalhos de segurança via `.htaccess`:

- **HTTPS forçado** — redirect automático de HTTP para HTTPS
- **HSTS** — Strict Transport Security com `includeSubDomains`
- **CSP** — Content Security Policy restritiva com exceções para o CMS e Google Maps
- **X-Content-Type-Options** — `nosniff`
- **X-Frame-Options** — `SAMEORIGIN`

As credenciais OAuth são injetadas durante o deploy e **nunca existem no código-fonte**.

---

## 📖 Documentação Adicional

| Documento                                                         | Descrição                              |
| ----------------------------------------------------------------- | -------------------------------------- |
| [COMO-ADICIONAR-NOTICIAS.md](docs/COMO-ADICIONAR-NOTICIAS.md)     | Como publicar notícias                 |
| [COMO-ADICIONAR-DOCUMENTOS.md](docs/COMO-ADICIONAR-DOCUMENTOS.md) | Como adicionar documentos PDF          |
| [BACKUPS.md](docs/BACKUPS.md)                                     | Estratégia de backups e recuperação    |
| [CI-CD.md](docs/CI-CD.md)                                         | Detalhes do pipeline e troubleshooting |

---

<div align="center">

Feito com ❤️ para a comunidade de Laranjeiro

</div>
