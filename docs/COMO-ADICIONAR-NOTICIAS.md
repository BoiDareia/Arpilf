# Como Adicionar Notícias

Guia passo-a-passo para publicar uma notícia no website da ARPILF.

## Resumo

Cada notícia é um ficheiro Markdown (`.md`) na pasta `content/noticias/`. Ao fazer push para o branch `main`, o pipeline publica automaticamente.

## Passo 1 — Criar o ficheiro Markdown

Na pasta `content/noticias/`, criar um ficheiro com nome descritivo em minúsculas, separado por hífens. Exemplo:

```text
content/noticias/almoco-natal-2025.md
```

> **Regras para o nome do ficheiro:**
>
> - Apenas letras minúsculas, números e hífens
> - Sem espaços, acentos ou caracteres especiais
> - O nome torna-se o URL da notícia (ex: `arpilf.pt/noticias/almoco-natal-2025/`)

## Passo 2 — Escrever o frontmatter

No início do ficheiro, adicionar o bloco de metadados entre `---`:

```yaml
---
title: "Almoço de Natal 2025"
date: 2025-12-20
description: "Resumo curto da notícia para listagens e SEO."
image: "/images/noticias/almoco-natal-2025.jpg"
tags: ["eventos", "comunidade"]
draft: false
---
```

| Campo         | Obrigatório | Descrição                                                    |
| ------------- | ----------- | ------------------------------------------------------------ |
| `title`       | Sim         | Título da notícia (aparece na página e na listagem)          |
| `date`        | Sim         | Data de publicação no formato `AAAA-MM-DD`                   |
| `description` | Sim         | Resumo curto (usado na listagem de notícias e meta tags SEO) |
| `image`       | Não         | Caminho para a imagem de destaque (ver Passo 3)              |
| `tags`        | Não         | Lista de etiquetas para categorizar a notícia                |
| `draft`       | Sim         | `false` para publicar, `true` para rascunho (não publicado)  |

## Passo 3 — Adicionar imagens (opcional)

1. Colocar a imagem na pasta `static/images/noticias/`
2. Usar nomes descritivos sem espaços (ex: `almoco-natal-2025.jpg`)
3. No frontmatter, referenciar com o caminho `/images/noticias/nome-da-imagem.jpg`
4. No corpo do texto, usar a sintaxe Markdown:

```markdown
![Descrição da imagem](/images/noticias/almoco-natal-2025.jpg)
```

> **Dica:** Otimizar as imagens antes de as adicionar (máx. ~500 KB). Ferramentas gratuitas: [Squoosh](https://squoosh.app/) ou [TinyPNG](https://tinypng.com/).

## Passo 4 — Escrever o conteúdo

Abaixo do frontmatter, escrever o texto da notícia em Markdown:

```markdown
---
title: "Almoço de Natal 2025"
date: 2025-12-20
description: "A ARPILF celebrou o Natal com um almoço especial."
image: "/images/noticias/almoco-natal-2025.jpg"
tags: ["eventos"]
draft: false
---

A ARPILF realizou o tradicional almoço de Natal no dia 20 de dezembro.

## Programa do Dia

O evento contou com música ao vivo e troca de presentes entre os utentes.

## Agradecimentos

Obrigado a todos os voluntários que ajudaram na organização!
```

### Formatação Markdown útil

| Sintaxe                 | Resultado        |
| ----------------------- | ---------------- |
| `**texto**`             | **negrito**      |
| `*texto*`               | _itálico_        |
| `## Título`             | Subtítulo        |
| `- item`                | Lista com pontos |
| `[texto](url)`          | Link             |
| `![descrição](caminho)` | Imagem           |

## Passo 5 — Testar localmente (opcional)

Se tiver o Hugo instalado localmente:

```bash
hugo server
```

Abrir `http://localhost:1313/noticias/` para verificar a notícia.

## Passo 6 — Publicar

```bash
git add content/noticias/almoco-natal-2025.md
git add static/images/noticias/almoco-natal-2025.jpg   # se adicionou imagem
git commit -m "Adicionar notícia: Almoço de Natal 2025"
git push origin main
```

O pipeline de CI/CD faz o build e deploy automaticamente. A notícia ficará disponível em poucos minutos.

## Editar ou Remover uma Notícia

- **Editar:** Alterar o ficheiro `.md`, fazer commit e push.
- **Ocultar temporariamente:** Mudar `draft: false` para `draft: true`, fazer commit e push.
- **Remover:** Apagar o ficheiro `.md` (e a imagem, se aplicável), fazer commit e push.

## Resolução de Problemas

| Problema                       | Solução                                                        |
| ------------------------------ | -------------------------------------------------------------- |
| Notícia não aparece no site    | Verificar que `draft: false` e que a `date` não é no futuro    |
| Imagem não aparece             | Confirmar que o caminho no frontmatter corresponde ao ficheiro |
| Erro no pipeline após push     | Verificar o frontmatter — todos os campos entre `---` e `---`  |
| Caracteres estranhos no título | Usar aspas à volta do título: `title: "O meu título"`          |
