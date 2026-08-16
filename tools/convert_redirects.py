#!/usr/bin/env python3
"""
convert_redirects.py
====================
Converte as paginas /r/ de redirects puros para paginas de produto completas.
Provider primario: Groq | Fallback: DeepSeek
Le as chaves do ficheiro .env automaticamente.

Uso:
    python tools/convert_redirects.py
    python tools/convert_redirects.py --limit 10
    python tools/convert_redirects.py --dry-run
"""

import re
import sys
import time
import json
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
from openai import OpenAI

REPO_ROOT      = Path(__file__).parent.parent
TOOLS_DIR      = REPO_ROOT / "tools"
REDIRECTS_DIR  = REPO_ROOT / "r"
PROGRESS_FILE  = TOOLS_DIR / "redirect_progress.json"
GROQ_MODELS = [
    "qwen/qwen3.6-27b",      # Recomendado Groq (primario)
    "openai/gpt-oss-120b",   # Recomendado Groq (secundario)
    "groq/compound",         # Fallback Groq extra
]
DEEPSEEK_MODEL = "deepseek-chat"

ENV_PATHS = [
    REPO_ROOT.parent / "Automacao" / "dealflow-bot" / ".env",
    REPO_ROOT.parent / "Automacao" / "Promoções automaticas" / "bot" / ".env",
    REPO_ROOT / ".env",
]

SYSTEM_PROMPT = (
    "Es um redator especializado em analise de produtos para consumidores portugueses. "
    "Escreves textos neutros, uteis e diretos. Portugues de Portugal correto e natural."
)

PROMPT_TPL = """Produto em promocao:
Titulo: {title}
Loja: {store}

Escreve um paragrafo editorial de 80 a 120 palavras em HTML simples.
- Comeca com <strong>Porque vale a pena:</strong>
- Explica o que e o produto e para quem e ideal
- Menciona que e uma oportunidade de poupanca
- Termina com: "Verifica o preco atual antes de comprar."
- Apenas o paragrafo (<strong>, <em> se necessario). Sem listas, sem links."""

PAGE_TPL = """\
<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title} | Descontos PT</title>
<meta name="description" content="{title} em promocao. Ve o preco atual e informacao antes de comprar."/>
<meta name="robots" content="index, follow"/>
<link rel="canonical" href="https://descontos-pt.github.io/r/{slug}/"/>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5696036221694738" crossorigin="anonymous"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root{{--bg:#f8fafc;--card:#fff;--accent:#ff5500;--text:#0f172a;--muted:#64748b;--line:#e2e8f0;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Outfit',sans-serif;background:var(--bg);color:var(--text);line-height:1.6;}}
.wrap{{max-width:820px;margin:0 auto;padding:24px 16px 80px;}}
header{{text-align:center;padding:18px;margin-bottom:24px;border-bottom:1px solid var(--line);}}
.logo{{font-size:26px;font-weight:900;}}.logo span{{color:var(--accent);}}
.logo a{{color:inherit;text-decoration:none;}}
.nav{{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:10px;}}
.nav a{{font-size:13px;font-weight:700;padding:6px 14px;border-radius:999px;border:1px solid var(--line);background:var(--card);text-decoration:none;color:var(--text);transition:all .15s;}}
.nav a:hover{{border-color:var(--accent);color:var(--accent);}}
.card{{background:var(--card);border-radius:20px;padding:24px;border:2px solid var(--accent);margin-bottom:24px;box-shadow:0 8px 24px rgba(255,85,0,.1);}}
.store-badge{{display:inline-block;background:var(--accent);color:#fff;font-size:12px;font-weight:800;padding:3px 12px;border-radius:8px;margin-bottom:12px;letter-spacing:.3px;}}
.prod-title{{font-size:21px;font-weight:800;line-height:1.4;margin-bottom:20px;}}
.buybtn{{display:block;background:linear-gradient(135deg,#ff5500,#ea580c);color:#fff!important;text-decoration:none;font-weight:800;font-size:16px;padding:15px 24px;border-radius:14px;text-align:center;margin-bottom:12px;box-shadow:0 6px 18px rgba(255,85,0,.3);transition:opacity .15s;}}
.buybtn:hover{{opacity:.88;}}
.disclaimer{{font-size:12.5px;color:var(--muted);padding-top:4px;}}
.editorial{{border-left:3px solid var(--accent);padding:16px 20px;background:#fff8f5;border-radius:0 14px 14px 0;margin-bottom:24px;font-size:15px;line-height:1.72;}}
.editorial strong{{color:var(--accent);}}
.back-link{{text-align:center;margin-bottom:32px;}}
.back-link a{{font-weight:700;color:var(--accent);text-decoration:none;}}
footer{{text-align:center;font-size:13px;color:var(--muted);padding-top:32px;border-top:1px solid var(--line);}}
footer a{{color:var(--muted);margin:0 8px;}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo"><a href="/">Descontos <span>PT</span></a></div>
    <nav class="nav">
      <a href="/">🏷️ Melhores Ofertas</a>
      <a href="/noticias/">📰 Notícias Tech</a>
      <a href="/guias/">📖 Guias de Poupança</a>
      <a href="/artigos/">🔒 Segurança</a>
      <a href="/sobre/">ℹ️ Sobre Nós</a>
    </nav>
  </header>

  <div class="card">
    <span class="store-badge">🛒 {store}</span>
    <h1 class="prod-title">{title}</h1>
    <a class="buybtn" href="{affiliate_url}" target="_blank" rel="noopener sponsored">
      Ver oferta em {store} →
    </a>
    <p class="disclaimer">⚠️ O preço pode ter mudado desde a publicação — confirma antes de comprar.</p>
  </div>

  <div class="editorial">
    {editorial}
  </div>

  <div class="back-link">
    <a href="/">← Ver todas as ofertas do dia</a>
  </div>

  <footer>
    <p>Como associados afiliados, podemos receber comissão por compras qualificadas, sem custo extra para ti.</p>
    <div style="margin-top:10px;">
      <a href="/sobre/">Sobre Nós</a>
      <a href="/privacy-policy/">Privacidade</a>
      <a href="/terms-of-service/">Termos</a>
    </div>
    <p style="margin-top:8px;">© 2026 Descontos PT</p>
  </footer>
</div>
</body>
</html>"""


def load_env():
    env = {}
    for ep in ENV_PATHS:
        if ep.exists():
            print(f"  .env: {ep.name} em {ep.parent.name}")
            for line in ep.read_text("utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
            break
    return env


def make_client(base_url, api_key):
    return OpenAI(api_key=api_key, base_url=base_url)


def extract_redirect(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    url  = ""
    refresh = soup.find("meta", {"http-equiv": "refresh"})
    if refresh:
        m = re.search(r"url=(.+)", refresh.get("content", ""), re.I)
        if m: url = m.group(1).strip()
    if not url:
        script = soup.find("script")
        if script:
            m = re.search(r'window\.location\.replace\(["\']([^"\']+)["\']', script.string or "")
            if m: url = m.group(1)

    title = soup.title.get_text(strip=True) if soup.title else "Produto em promoção"
    title = re.sub(r"\s*[\|–-].*$", "", title).strip()
    if not title: title = "Produto em promoção"

    store = "Amazon"
    if "aliexpress" in url: store = "AliExpress"
    elif "awin"     in url: store = "Parceiro AWIN"

    return {"url": url, "title": title, "store": store}


def call_ai(clients, title, store):
    prompt = PROMPT_TPL.format(title=title[:200], store=store)
    for label, client, model in clients:
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.72, max_tokens=280,
            )
            text = r.choices[0].message.content.strip()
            if text: return text, label
        except Exception as e:
            print(f"    [{label}/{model}] {type(e).__name__}: {str(e)[:70]}")
            time.sleep(1.5)
    fallback = f"<strong>Porque vale a pena:</strong> Produto em promoção disponível em {store}. Verifica o preço atual antes de comprar."
    return fallback, "fallback"


def load_progress():
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text("utf-8"))
    return {"done": [], "failed": []}

def save_progress(p):
    PROGRESS_FILE.parent.mkdir(exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(p, indent=2, ensure_ascii=False), "utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit",   type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force",   action="store_true")
    ap.add_argument("--delay",   type=float, default=0.8)
    args = ap.parse_args()

    print("\n=== CONVERTER PAGINAS /r/ ===\n")

    env = load_env()
    clients = []
    groq_key     = env.get("GROQ_API_KEY", "")
    deepseek_key = env.get("DEEPSEEK_API_KEY", "")

    if groq_key:
        groq_client = make_client("https://api.groq.com/openai/v1", groq_key)
        for model in GROQ_MODELS:
            clients.append((f"Groq/{model.split('/')[-1]}", groq_client, model))
        print(f"  Groq:     OK — {' → '.join(m.split('/')[-1] for m in GROQ_MODELS)}")
    if deepseek_key:
        clients.append(("DeepSeek", make_client("https://api.deepseek.com", deepseek_key), DEEPSEEK_MODEL))
        print(f"  DeepSeek: OK [fallback final]")
    if not clients and not args.dry_run:
        print("ERRO: Nenhuma chave de IA encontrada."); sys.exit(1)

    progress = load_progress()
    entries  = [(d.name, d / "index.html") for d in sorted(REDIRECTS_DIR.iterdir()) if (d / "index.html").exists()]
    if args.limit: entries = entries[:args.limit]

    total = len(entries)
    done = skip = fail = 0
    print(f"\n  Paginas /r/ encontradas: {total}\n")

    for i, (slug, fp) in enumerate(entries, 1):
        print(f"[{i:03d}/{total}] /r/{slug}", end="  ")

        if slug in progress["done"] and not args.force:
            print("skip"); skip += 1; continue

        html = fp.read_text("utf-8", errors="replace")
        data = extract_redirect(html)

        if not data["url"]:
            print("sem URL, skip"); fail += 1; continue

        print(f"-> \"{data['title'][:50]}\"", end="  ")

        if args.dry_run:
            print("[dry-run]"); done += 1; continue

        editorial, provider = call_ai(clients, data["title"], data["store"])
        page = PAGE_TPL.format(
            slug=slug, title=data["title"], store=data["store"],
            affiliate_url=data["url"], editorial=editorial,
        )
        fp.write_text(page, "utf-8")
        progress["done"].append(slug)
        save_progress(progress)
        done += 1
        print(f"OK [{provider}]")
        time.sleep(args.delay)

    print(f"\n  Convertidas: {done} | Saltadas: {skip} | Erros: {fail}")
    if not args.dry_run and done:
        print("  Proximo passo: python tools/publish.py")


if __name__ == "__main__":
    main()
