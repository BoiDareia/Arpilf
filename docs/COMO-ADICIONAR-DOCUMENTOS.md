# Como Adicionar Documentos

Guia passo-a-passo para adicionar ou atualizar documentos PDF no website da ARPILF.

## Resumo

Os documentos PDF ficam em `static/documentos/` e os seus metadados em `data/documentos.yaml`. Ao fazer push para `main`, o pipeline publica automaticamente.

## Categorias Disponíveis

| Categoria              | Pasta                                       |
| ---------------------- | ------------------------------------------- |
| Relatórios Financeiros | `static/documentos/relatorios-financeiros/` |
| Regulamentos           | `static/documentos/regulamentos/`           |
| Estatutos              | `static/documentos/estatutos/`              |
| Planos de Ação         | `static/documentos/planos-acao/`            |
| Fichas de Inscrição    | `static/documentos/fichas-inscricao/`       |
| Outros Documentos      | `static/documentos/outros/`                 |

## Passo 1 — Colocar o PDF na pasta correta

Copiar o ficheiro PDF para a subpasta da categoria correspondente. Exemplo:

```text
static/documentos/relatorios-financeiros/Publicacao_contas_2025.pdf
```

> **Regras para o nome do ficheiro:**
>
> - Evitar espaços (usar `_` ou `-`)
> - Evitar acentos e caracteres especiais
> - Manter um nome descritivo e consistente com os existentes

## Passo 2 — Atualizar o ficheiro documentos.yaml

Abrir `data/documentos.yaml` e adicionar uma entrada na categoria correta.

### Exemplo: adicionar "Publicação de Contas 2025"

Antes:

```yaml
categorias:
  - nome: "Relatórios Financeiros"
    slug: "relatorios-financeiros"
    documentos:
      - titulo: "Publicação de Contas 2024"
        ficheiro: "/documentos/relatorios-financeiros/Publicacao_contas_2024.pdf"
        data: "2025-03-15"
```

Depois:

```yaml
categorias:
  - nome: "Relatórios Financeiros"
    slug: "relatorios-financeiros"
    documentos:
      - titulo: "Publicação de Contas 2025"
        ficheiro: "/documentos/relatorios-financeiros/Publicacao_contas_2025.pdf"
        data: "2026-03-15"
      - titulo: "Publicação de Contas 2024"
        ficheiro: "/documentos/relatorios-financeiros/Publicacao_contas_2024.pdf"
        data: "2025-03-15"
```

### Estrutura de cada entrada

```yaml
- titulo: "Nome do Documento"
  ficheiro: "/documentos/CATEGORIA/nome_do_ficheiro.pdf"
  data: "AAAA-MM-DD"
```

| Campo      | Descrição                                                              |
| ---------- | ---------------------------------------------------------------------- |
| `titulo`   | Nome legível do documento (aparece na página)                          |
| `ficheiro` | Caminho do PDF — começa com `/documentos/` seguido da pasta e ficheiro |
| `data`     | Data do documento no formato `AAAA-MM-DD`                              |

> **Atenção à indentação!** O YAML usa espaços (não tabs). Cada nível de indentação usa 2 ou 4 espaços. Manter consistente com as entradas existentes.

## Passo 3 — Testar localmente (opcional)

```bash
hugo server
```

Abrir `http://localhost:1313/documentos/` e verificar que o novo documento aparece na categoria correta com link funcional.

## Passo 4 — Publicar

```bash
git add static/documentos/relatorios-financeiros/Publicacao_contas_2025.pdf
git add data/documentos.yaml
git commit -m "Adicionar Publicação de Contas 2025"
git push origin main
```

O pipeline faz o build e deploy automaticamente.

## Atualizar um Documento Existente

1. Substituir o ficheiro PDF na mesma pasta (manter o mesmo nome)
2. Se necessário, atualizar a `data` em `documentos.yaml`
3. Fazer commit e push

## Remover um Documento

1. Apagar o ficheiro PDF da pasta `static/documentos/`
2. Remover a entrada correspondente em `data/documentos.yaml`
3. Fazer commit e push

## Resolução de Problemas

| Problema                        | Solução                                                               |
| ------------------------------- | --------------------------------------------------------------------- |
| Documento não aparece na página | Verificar que o caminho em `ficheiro` corresponde ao ficheiro real    |
| Erro no pipeline após push      | Verificar a indentação do YAML — usar espaços, não tabs               |
| Link de download não funciona   | Confirmar que o caminho começa com `/documentos/` e o ficheiro existe |
| Página de documentos vazia      | Verificar que `data/documentos.yaml` não tem erros de sintaxe         |
