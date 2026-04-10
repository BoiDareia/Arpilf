# Pipeline CI/CD

Explicação do pipeline de integração contínua e deploy automático do website ARPILF.

## Como Funciona

O pipeline é executado automaticamente pelo GitHub Actions sempre que se faz push para o branch `main`. O ficheiro de configuração está em `.github/workflows/deploy.yml`.

### Fluxo do Pipeline

```text
Push para main
  → Checkout do código
  → Instalar Hugo
  → Descarregar Tailwind CSS CLI
  → Compilar CSS (Tailwind, minificado)
  → Build Hugo (HTML estático, minificado)
  → Validar HTML
  → Lighthouse CI (performance, acessibilidade, SEO)
  → Deploy via SFTP para o cPanel
```

Se qualquer passo falhar, o pipeline para e o deploy **não acontece**. O site mantém a versão anterior.

## Passos do Pipeline em Detalhe

| Passo                 | O que faz                                                         |
| --------------------- | ----------------------------------------------------------------- |
| Checkout              | Descarrega o código do repositório                                |
| Setup Hugo            | Instala o Hugo (extended edition) no runner                       |
| Download Tailwind CLI | Descarrega o binário standalone do Tailwind CSS                   |
| Build Tailwind CSS    | Compila `assets/css/main.css` → `static/css/style.css` (minified) |
| Build Hugo            | Gera o site estático em `public/` com `hugo --minify`             |
| Validar HTML          | Verifica erros no HTML gerado (html5validator)                    |
| Lighthouse CI         | Testa performance, acessibilidade e SEO (mínimo 90 pontos)        |
| Deploy SFTP           | Envia `public/` para `public_html/` no cPanel via lftp            |

## Variáveis de Ambiente (GitHub Secrets)

O pipeline precisa de 4 secrets configurados no repositório GitHub.

**Onde configurar:** GitHub → Settings → Secrets and variables → Actions → New repository secret

| Secret          | Descrição                   | Exemplo                |
| --------------- | --------------------------- | ---------------------- |
| `SFTP_HOST`     | Hostname do servidor cPanel | `ftp.arpilf.pt`        |
| `SFTP_USER`     | Utilizador SFTP do cPanel   | `arpilf`               |
| `SFTP_PASSWORD` | Password SFTP do cPanel     | _(password do cPanel)_ |
| `SFTP_PATH`     | Caminho remoto no servidor  | `/public_html/`        |

> **Segurança:** Os secrets ficam encriptados no GitHub e nunca aparecem nos logs do pipeline. Nunca colocar credenciais diretamente no código.

### Como atualizar um secret

1. Ir a **Settings → Secrets and variables → Actions** no repositório GitHub
2. Clicar no secret a atualizar
3. Clicar em **Update** e introduzir o novo valor
4. Guardar

## Troubleshooting — Resolver Falhas

### Onde ver os logs

1. Ir ao repositório no GitHub
2. Clicar no separador **Actions**
3. Clicar no workflow run que falhou (ícone ❌ vermelho)
4. Clicar no job **build-and-deploy** para ver os logs detalhados de cada passo

### Problemas Comuns

#### Build Hugo falha

**Sintoma:** Erro no passo "Build Hugo".

**Causas possíveis:**

- Frontmatter inválido num ficheiro Markdown (falta `---` de fecho, campo mal formatado)
- Template com erro de sintaxe em `layouts/`

**Solução:**

1. Ler a mensagem de erro nos logs — o Hugo indica o ficheiro e a linha com problema
2. Corrigir o ficheiro localmente
3. Testar com `hugo server` antes de fazer push
4. Fazer commit e push da correção

#### Validação HTML falha

**Sintoma:** Erro no passo "Validate HTML".

**Causas possíveis:**

- HTML inválido gerado por um template
- Tag não fechada ou atributo em falta

**Solução:**

1. Verificar nos logs qual ficheiro HTML tem o erro
2. Corrigir o template correspondente em `layouts/`
3. Fazer commit e push

#### Deploy SFTP falha

**Sintoma:** Erro no passo "Deploy via SFTP".

**Causas possíveis:**

- Credenciais SFTP expiradas ou incorretas
- Servidor cPanel temporariamente indisponível
- Caminho `SFTP_PATH` incorreto

**Solução:**

1. Verificar que os GitHub Secrets estão corretos (atualizar se necessário)
2. Testar a ligação SFTP manualmente (ex: com FileZilla)
3. Contactar o suporte da online.pt se o servidor estiver em baixo
4. Re-executar o pipeline: no GitHub Actions, clicar **Re-run all jobs**

#### Lighthouse CI falha

**Sintoma:** Erro no passo "Lighthouse CI" — scores abaixo de 90.

**Causas possíveis:**

- Imagens muito grandes (sem otimização)
- CSS ou JavaScript demasiado pesado
- Falta de atributos `alt` em imagens
- Falta de meta tags

**Solução:**

1. Verificar nos logs quais auditorias falharam
2. Otimizar imagens (comprimir, redimensionar)
3. Verificar que todas as `<img>` têm atributo `alt`
4. Fazer commit e push das correções

### Re-executar o Pipeline

Se o problema foi temporário (ex: servidor indisponível):

1. Ir a **Actions** no GitHub
2. Clicar no workflow run que falhou
3. Clicar em **Re-run all jobs**

O pipeline volta a executar todos os passos desde o início.

## Fluxo de Trabalho Recomendado

1. Fazer alterações localmente (editar Markdown, adicionar PDFs, etc.)
2. Testar com `hugo server` localmente
3. Fazer commit e push para `main`
4. Verificar no separador **Actions** que o pipeline passou (ícone ✅ verde)
5. Confirmar no site `arpilf.pt` que as alterações estão publicadas
