# ARPILF — Website

Website da ARPILF — Associação de Reformados, Pensionistas e Idosos.

Site estático gerado com [Hugo](https://gohugo.io/) e estilizado com [Tailwind CSS](https://tailwindcss.com/) (CLI standalone). Deploy automatizado via GitHub Actions → SFTP para o cPanel da online.pt.

## Pré-requisitos

- [Hugo](https://gohugo.io/installation/) (extended edition, versão mais recente)
- [Tailwind CSS CLI standalone](https://github.com/tailwindlabs/tailwindcss/releases) — binário único, sem necessidade de Node.js
- [Git](https://git-scm.com/)
- (Opcional) [Node.js](https://nodejs.org/) — apenas para executar testes JavaScript localmente
- (Opcional) [PHP 8+](https://www.php.net/) — apenas para testar o formulário de contacto localmente
- (Opcional) [Python 3.10+](https://www.python.org/) + pytest + Hypothesis — para testes de build

## Setup Local

### 1. Clonar o repositório

```bash
git clone https://github.com/<org>/Arpilf.git
cd Arpilf
```

### 2. Instalar o Tailwind CSS CLI standalone

Descarregar o binário para a raiz do projeto `Arpilf/`:

```bash
# Linux
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
chmod +x tailwindcss-linux-x64
mv tailwindcss-linux-x64 tailwindcss

# macOS (Apple Silicon)
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
chmod +x tailwindcss-macos-arm64
mv tailwindcss-macos-arm64 tailwindcss

# macOS (Intel)
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-x64
chmod +x tailwindcss-macos-x64
mv tailwindcss-macos-x64 tailwindcss
```

### 3. Compilar o CSS

Desenvolvimento (com watch — recompila automaticamente ao guardar):

```bash
./tailwindcss -i assets/css/main.css -o static/css/style.css --watch
```

Produção (minificado):

```bash
./tailwindcss -i assets/css/main.css -o static/css/style.css --minify
```

### 4. Iniciar o servidor de desenvolvimento Hugo

Numa janela de terminal separada:

```bash
hugo server
```

O site fica disponível em `http://localhost:1313/`. O Hugo recarrega automaticamente ao detetar alterações.

## Comandos de Build

| Comando                                                                 | Descrição                                    |
| ----------------------------------------------------------------------- | -------------------------------------------- |
| `hugo server`                                                           | Servidor de desenvolvimento com live reload  |
| `hugo`                                                                  | Build de produção → gera `public/`           |
| `hugo --minify`                                                         | Build de produção com HTML/CSS/JS minificado |
| `./tailwindcss -i assets/css/main.css -o static/css/style.css --watch`  | Compilar Tailwind em modo watch              |
| `./tailwindcss -i assets/css/main.css -o static/css/style.css --minify` | Compilar Tailwind minificado                 |

## Estrutura do Projeto

```text
Arpilf/
├── hugo.toml                    # Configuração principal Hugo
├── tailwind.config.js           # Configuração Tailwind CSS
├── package.json                 # Dependências de teste (Vitest, fast-check)
├── .github/workflows/
│   └── deploy.yml               # Pipeline CI/CD (GitHub Actions)
├── assets/
│   └── css/main.css             # Diretivas Tailwind (input)
├── content/                     # Conteúdo Markdown
│   ├── _index.md                # Homepage
│   ├── sobre/                   # Sobre Nós
│   ├── servicos/                # Serviços
│   ├── noticias/                # Artigos de notícias
│   ├── documentos/              # Página de documentos
│   ├── contactos/               # Contactos + obrigado/erro
│   ├── donativos/               # Donativos
│   └── protecao-dados/          # Política RGPD
├── data/
│   └── documentos.yaml          # Catálogo de documentos (metadados)
├── layouts/                     # Templates Hugo
│   ├── _default/                # Templates base (baseof, single, list)
│   ├── partials/                # Partials (head, nav, footer, chatbot)
│   ├── noticias/                # Templates de notícias
│   ├── documentos/              # Template de documentos
│   ├── contactos/               # Template de contactos
│   ├── index.html               # Template da homepage
│   └── 404.html                 # Página 404
├── static/                      # Ficheiros estáticos (copiados tal qual)
│   ├── css/style.css            # CSS compilado (gerado pelo Tailwind)
│   ├── js/                      # JavaScript (main, chatbot, contact-form)
│   ├── images/                  # Imagens (logo, notícias)
│   ├── documentos/              # PDFs organizados por categoria
│   ├── contact.php              # Handler PHP do formulário
│   └── .htaccess                # Redirects, segurança, cache
├── tests/                       # Testes
│   ├── build/                   # Testes Python (pytest/Hypothesis)
│   ├── js/                      # Testes JavaScript (Vitest/fast-check)
│   └── php/                     # Testes PHP (PHPUnit/Eris)
├── docs/                        # Documentação operacional
└── public/                      # Output do build (não versionar)
```

## Deploy

### Deploy Automático (CI/CD)

O deploy é feito automaticamente via GitHub Actions quando se faz push para o branch `main`. O pipeline:

1. Faz checkout do repositório
2. Instala o Hugo (extended edition)
3. Descarrega o Tailwind CSS CLI standalone
4. Compila o Tailwind CSS (minificado)
5. Executa o build Hugo (`hugo --minify`)
6. Valida o HTML gerado
7. Executa Lighthouse CI (scores mínimos de 90)
8. Faz deploy via SFTP (lftp) para o cPanel da online.pt

### GitHub Secrets Necessários

Configurar em **Settings → Secrets and variables → Actions** no repositório GitHub:

| Secret          | Descrição                                         |
| --------------- | ------------------------------------------------- |
| `SFTP_HOST`     | Hostname do servidor cPanel (ex: `ftp.arpilf.pt`) |
| `SFTP_USER`     | Utilizador SFTP do cPanel                         |
| `SFTP_PASSWORD` | Password SFTP do cPanel                           |
| `SFTP_PATH`     | Caminho remoto no servidor (ex: `/public_html/`)  |

### Deploy Manual (alternativa)

Se necessário fazer deploy manual sem o pipeline:

```bash
# 1. Compilar Tailwind CSS
./tailwindcss -i assets/css/main.css -o static/css/style.css --minify

# 2. Build Hugo
hugo --minify

# 3. Enviar ficheiros via SFTP/FTP
# Copiar todo o conteúdo de public/ para public_html/ no cPanel
# Pode usar FileZilla, lftp, ou o gestor de ficheiros do cPanel
```

Exemplo com `lftp`:

```bash
lftp -e "
  set sftp:auto-confirm yes;
  mirror --reverse --delete --verbose --parallel=4 \
    ./public/ /public_html/;
  bye
" -u UTILIZADOR,PASSWORD sftp://HOSTNAME
```

## Testes

```bash
# Testes JavaScript (chatbot, formulário)
npm install
npm run test:js

# Testes Python (build Hugo, redirects)
pip install pytest hypothesis beautifulsoup4 lxml pyyaml
pytest tests/build/

# Testes PHP (handler do formulário) — requer PHPUnit + Eris
cd tests/php && phpunit
```

## Documentação Adicional

Consultar a pasta `docs/` para guias operacionais:

- `COMO-ADICIONAR-NOTICIAS.md` — Como publicar notícias
- `COMO-ADICIONAR-DOCUMENTOS.md` — Como adicionar documentos PDF
- `BACKUPS.md` — Estratégia de backups e recuperação
- `CI-CD.md` — Detalhes do pipeline e troubleshooting
