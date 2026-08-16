# 🛠️ Tools — Automação AdSense

Scripts para tornar o site conforme com o Google AdSense,
adicionando texto editorial gerado por IA às páginas de produto.

## Dependências

```bash
pip install openai beautifulsoup4 lxml
```

## Uso Completo (ordem recomendada)

### Passo 1 — Enriquecer as 200 páginas /d/

```bash
# Testar primeiro sem alterar nada
python tools/enrich_products.py --api-key TUA_CHAVE --limit 5 --dry-run

# Processar tudo (demora ~4-5 min para 200 páginas)
python tools/enrich_products.py --api-key TUA_CHAVE

# Processar em lotes se necessário
python tools/enrich_products.py --api-key TUA_CHAVE --limit 50
python tools/enrich_products.py --api-key TUA_CHAVE --limit 50  # retoma do ponto anterior
```

### Passo 2 — Converter as 98 páginas /r/ (redirects → páginas reais)

```bash
python tools/convert_redirects.py --api-key TUA_CHAVE
```

### Passo 3 — Publicar para o GitHub

```bash
python tools/publish.py
```

## Chave API DeepSeek

Obtém a tua chave em: https://platform.deepseek.com/api_keys

Custo estimado para processar 298 páginas: ~0,30-0,60 USD

## Progresso

O script guarda o progresso em `tools/enrichment_progress.json`.
Se o script parar a meio, podes correr de novo — salta automaticamente
as páginas já processadas.

## O que cada script faz

| Script | Objetivo | Páginas |
|--------|----------|---------|
| `enrich_products.py` | Adiciona descrição editorial às /d/ | 200 |
| `convert_redirects.py` | Converte /r/ de redirect para página completa | 98 |
| `publish.py` | Git add + commit + push para GitHub | — |
