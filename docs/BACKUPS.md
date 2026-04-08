# Backups e Recuperação

Estratégia de backups do website ARPILF e procedimentos de recuperação.

## Estratégia de Backups

O website tem duas camadas de proteção:

### 1. Git como backup de código e conteúdo

Todo o código-fonte, conteúdo Markdown, templates e configurações estão versionados no repositório GitHub. Isto significa que:

- Cada alteração fica registada no histórico do Git
- É possível reverter para qualquer versão anterior
- O repositório GitHub serve como backup remoto permanente
- Múltiplas pessoas podem ter cópias locais do repositório

**O que está no Git:**

- Conteúdo das páginas (`content/`)
- Metadados dos documentos (`data/documentos.yaml`)
- Templates e layouts (`layouts/`)
- Configuração (`hugo.toml`, `tailwind.config.js`)
- CSS e JavaScript (`assets/`, `static/js/`)
- Documentos PDF (`static/documentos/`)
- Pipeline CI/CD (`.github/workflows/`)
- Documentação (`docs/`, `README.md`)

### 2. Backups automáticos do cPanel (online.pt)

O alojamento cPanel da online.pt inclui backups automáticos:

- **Frequência:** Diária (configuração padrão do cPanel)
- **Conteúdo:** Ficheiros em `public_html/`, bases de dados, emails, configurações
- **Retenção:** Conforme o plano de alojamento (consultar painel cPanel)
- **Acesso:** Painel cPanel → Backups → Download de backup completo ou parcial

> **Nota:** Os backups do cPanel protegem os ficheiros publicados no servidor. O Git protege o código-fonte e o histórico de alterações.

## Procedimentos de Recuperação

### Cenário 1 — Reverter uma alteração recente

Se uma alteração causou problemas no site:

```bash
# Ver histórico de commits
git log --oneline -10

# Reverter o último commit (mantém as alterações como não commitadas)
git revert HEAD

# Ou reverter para um commit específico
git revert <hash-do-commit>

# Publicar a reversão
git push origin main
```

O pipeline faz o build e deploy da versão corrigida automaticamente.

### Cenário 2 — Restaurar o site a partir do Git

Se o servidor ficou corrompido mas o repositório está intacto:

```bash
# Clonar o repositório
git clone https://github.com/<org>/Arpilf.git
cd Arpilf

# Compilar o CSS
./tailwindcss -i assets/css/main.css -o static/css/style.css --minify

# Build Hugo
hugo --minify

# Fazer upload de public/ para o servidor via SFTP
# (ver README.md secção "Deploy Manual")
```

Ou simplesmente fazer push de qualquer alteração para `main` — o pipeline reconstrói e faz deploy de tudo.

### Cenário 3 — Restaurar a partir do backup cPanel

Se tanto o servidor como o repositório tiverem problemas:

1. Aceder ao painel cPanel da online.pt
2. Ir a **Backups** (ou **JetBackup** se disponível)
3. Selecionar a data do backup pretendido
4. Restaurar os ficheiros de `public_html/`

### Cenário 4 — Perda do repositório GitHub

Se o repositório GitHub for apagado ou ficar inacessível:

1. Qualquer clone local contém o histórico completo do Git
2. Criar um novo repositório no GitHub
3. Fazer push do clone local para o novo repositório
4. Atualizar os GitHub Secrets (SFTP_HOST, SFTP_USER, SFTP_PASSWORD, SFTP_PATH)
5. O pipeline volta a funcionar normalmente

## Boas Práticas

- **Manter um clone local atualizado** — fazer `git pull` regularmente no computador pessoal
- **Não apagar branches sem necessidade** — o histórico do Git é o melhor seguro
- **Verificar os backups do cPanel** — confirmar periodicamente que os backups automáticos estão ativos no painel
- **Testar localmente antes de publicar** — usar `hugo server` para verificar alterações antes do push

## Contactos de Emergência

| Situação                         | Contacto                              |
| -------------------------------- | ------------------------------------- |
| Problema com o alojamento        | Suporte online.pt (painel de cliente) |
| Problema com o repositório       | Administrador do repositório GitHub   |
| Problema com o domínio arpilf.pt | Registar do domínio / online.pt       |
