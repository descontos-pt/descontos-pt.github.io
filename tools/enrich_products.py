#!/usr/bin/env python3
# GROQ MODELS UPDATED 2026-08-16 (llama-3.3-70b descomissionado)
"""
enrich_products.py
==================
Enriquece as paginas /d/*.html com descricoes editoriais geradas por IA.
Provider primario: Groq (gratis, llama-3.3-70b).
Provider fallback: DeepSeek (pago, economico).
Le as chaves do ficheiro .env automaticamente.

Uso:
    python tools/enrich_products.py              # processa tudo
    python tools/enrich_products.py --limit 10   # so os primeiros 10
    python tools/enrich_products.py --dry-run    # simula sem chamar IA
    python tools/enrich_products.py --force      # re-processa ja feitas
"""

import re
import sys
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import time
import json
import argparse
from pathlib import Path
from bs4 import BeautifulSoup

# --- localizar o .env no projeto ---
REPO_ROOT     = Path(__file__).parent.parent
TOOLS_DIR     = REPO_ROOT / "tools"
DEALS_DIR     = REPO_ROOT / "d"
PROGRESS_FILE = TOOLS_DIR / "enrichment_progress.json"
INJECT_MARKER = "<!-- AI_DESC -->"
INSERT_BEFORE = '<div class="panel">'

# Caminho do .env (dealflow-bot)
ENV_PATHS = [
    REPO_ROOT.parent / "Automacao" / "dealflow-bot" / ".env",
    REPO_ROOT.parent / "Automacao" / "Promoções automaticas" / "bot" / ".env",
    REPO_ROOT / ".env",
    Path.home() / ".env",
]


def load_env():
    """Carrega variaveis do .env sem dependencias externas."""
    env = {}
    for ep in ENV_PATHS:
        if ep.exists():
            print(f"  .env encontrado: {ep}")
            for line in ep.read_text("utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
            break
    return env


def make_groq_client(api_key: str):
    from openai import OpenAI
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )


def make_deepseek_client(api_key: str):
    from openai import OpenAI
    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )


# Modelos por provider
# Modelos por ordem de prioridade (llama-3.3-70b descomissionado em 2026-08-16)
GROQ_MODELS = [
    "qwen/qwen3.6-27b",      # Recomendado Groq (primario)
    "openai/gpt-oss-120b",   # Recomendado Groq (secundario)
    "groq/compound",         # Fallback Groq extra
]
DEEPSEEK_MODEL = "deepseek-chat"

SYSTEM_PROMPT = (
    "Es um redator especializado em analise de produtos para consumidores portugueses. "
    "Escreves textos neutros, uteis e diretos. Portugues de Portugal correto e natural."
)

PROMPT_TPL = """Produto em promocao:
Titulo: {title}
Preco atual: {price}  |  Preco anterior: {old_price}  |  Desconto: {discount}
Categoria: {category}
Loja: {store}

Escreve um paragrafo editorial de 90 a 130 palavras em HTML simples.
- Comeca com <strong>Porque vale a pena:</strong>
- Explica o que e o produto e para quem e ideal (sem inventar especificacoes)
- Comenta o desconto de forma contextualizada
- Termina com: "Consulta sempre o historico de preco antes de comprar."
- Sem link de compra, sem listas, sem cabecalhos extra
- Apenas o paragrafo em HTML simples (<strong>, <em> se necessario)"""

EDITORIAL_CSS = """    <style>
      .editorial-panel{border-left:3px solid var(--accent,#ff5500);margin-bottom:0;}
      .editorial-desc{font-size:15px;line-height:1.72;color:var(--text,#0f172a);padding:2px 0;}
      .editorial-desc strong{color:var(--accent,#ff5500);}
    </style>"""

BLOCK = """\n    {marker}\n    <div class="panel editorial-panel">\n      <div class="editorial-desc">{text}</div>\n    </div>\n"""


def extract_data(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # Titulo
    title = ""
    t = soup.find("title")
    if t:
        title = re.sub(r"\s*por\s+[\d,.]+\s*[\u20ac€].*$", "", t.get_text(), flags=re.I)
        title = re.sub(r"\s*\|.*$", "", title).strip()

    # Preco novo
    price = ""
    for cls in ["new-price", "price-new", "novo-preco", "price"]:
        el = soup.find(class_=cls)
        if el:
            price = el.get_text(strip=True); break

    # Preco antigo
    old_price = ""
    for cls in ["old-price", "price-old", "preco-antigo"]:
        el = soup.find(class_=cls)
        if el:
            old_price = el.get_text(strip=True); break

    # Desconto
    discount = ""
    disc = soup.find(class_=re.compile(r"^disc"))
    if disc:
        discount = disc.get_text(strip=True)

    # Fallback: meta description
    meta = soup.find("meta", {"name": "description"})
    meta_text = meta.get("content", "") if meta else ""
    if not price:
        m = re.search(r"([\d,.]+\s*[\u20ac€])", meta_text)
        if m: price = m.group(1)
    if not old_price:
        m = re.search(r"antes\s+([\d,.]+\s*[\u20ac€])", meta_text, re.I)
        if m: old_price = m.group(1)
    if not discount:
        m = re.search(r"(-\d+%)", meta_text)
        if m: discount = m.group(1)

    # Loja
    store = "Amazon"
    btn = soup.find("a", class_="buybtn") or soup.find("a", string=re.compile(r"Ver oferta", re.I))
    if btn:
        href = btn.get("href", "")
        if "aliexpress" in href: store = "AliExpress"
        elif "awin" in href:    store = "Parceiro AWIN"

    # Categoria
    cat = ""
    for cls in ["cat", "badge", "category"]:
        el = soup.find(class_=re.compile(cls, re.I))
        if el:
            cat = el.get_text(strip=True)[:80]; break

    return {
        "title"    : title[:200] or "Produto em promoção",
        "price"    : price     or "ver página",
        "old_price": old_price or "N/D",
        "discount" : discount  or "N/D",
        "category" : cat       or "Geral",
        "store"    : store,
    }


def call_ai(clients: list, product: dict) -> str:
    """Tenta cada modelo em cascata: Qwen → GPT-OSS → DeepSeek."""
    prompt = PROMPT_TPL.format(**product)
    for label, client, model in clients:
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.72,
                max_tokens=320,
            )
            text = r.choices[0].message.content.strip()
            if text:
                return text, label
        except Exception as e:
            err = str(e)[:90]
            print(f"    [{label}/{model}] {type(e).__name__}: {err}")
            time.sleep(1.5)
    return "", "none"


def inject(html: str, text: str) -> str:
    if ".editorial-panel" not in html:
        html = html.replace("</head>", EDITORIAL_CSS + "\n</head>", 1)
    block = BLOCK.format(marker=INJECT_MARKER, text=text)
    if INSERT_BEFORE in html:
        return html.replace(INSERT_BEFORE, block + "    " + INSERT_BEFORE, 1)
    for fb in ["</main>", "</body>"]:
        if fb in html:
            return html.replace(fb, block + fb, 1)
    return html + block


def load_progress():
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text("utf-8"))
    return {"done": [], "failed": []}


def save_progress(p):
    PROGRESS_FILE.parent.mkdir(exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(p, indent=2, ensure_ascii=False), "utf-8")


def main():
    ap = argparse.ArgumentParser(description="Enriquecer /d/ com descricoes IA (Groq → DeepSeek)")
    ap.add_argument("--limit",   type=int, default=0,     help="Max paginas (0=todas)")
    ap.add_argument("--dry-run", action="store_true",     help="Nao guarda ficheiros")
    ap.add_argument("--force",   action="store_true",     help="Re-processa ja feitas")
    ap.add_argument("--delay",   type=float, default=0.8, help="Delay entre chamadas (seg)")
    args = ap.parse_args()

    print("\n=== ENRIQUECER PAGINAS /d/ ===\n")

    # Carregar .env
    env = load_env()
    groq_key     = env.get("GROQ_API_KEY", "")
    deepseek_key = env.get("DEEPSEEK_API_KEY", "")

    # Construir lista de clientes por ordem de prioridade
    clients = []
    if groq_key:
        groq_client = make_groq_client(groq_key)
        for model in GROQ_MODELS:
            clients.append((f"Groq/{model.split('/')[-1]}", groq_client, model))
        print(f"  Groq:     OK — cascata: {' → '.join(m.split('/')[-1] for m in GROQ_MODELS)}")
    else:
        print("  Groq:     sem chave")

    if deepseek_key and deepseek_key not in ("TUA_CHAVE_DEEPSEEK", ""):
        clients.append(("DeepSeek", make_deepseek_client(deepseek_key), DEEPSEEK_MODEL))
        print(f"  DeepSeek: OK [fallback final]")
    else:
        print("  DeepSeek: sem chave")

    if not clients and not args.dry_run:
        print("\nERRO: Nenhuma chave de IA encontrada no .env")
        sys.exit(1)

    progress = load_progress()
    files    = sorted(DEALS_DIR.glob("*.html"))
    if args.limit:
        files = files[:args.limit]

    total = len(files)
    done = skip = fail = 0
    provider_stats = {}

    print(f"\n  Paginas /d/ encontradas: {total}")
    if args.dry_run: print("  MODO: dry-run\n")
    else:            print()

    for i, fp in enumerate(files, 1):
        name = fp.name
        print(f"[{i:03d}/{total}] {name}", end="  ")

        if name in progress["done"] and not args.force:
            print("skip (ja feita)")
            skip += 1
            continue

        html = fp.read_text("utf-8", errors="replace")
        if INJECT_MARKER in html and not args.force:
            print("skip (marcador ok)")
            progress["done"].append(name)
            skip += 1
            continue

        prod = extract_data(html)
        preview = prod["title"][:50].encode("ascii", "replace").decode("ascii")
        print(f"-> \"{preview}\"", end="  ")

        if args.dry_run:
            print("[dry-run]")
            done += 1
            continue

        text, provider = call_ai(clients, prod)
        if not text:
            print("FALHOU (todos os providers)")
            progress["failed"].append(name)
            fail += 1
            save_progress(progress)
            time.sleep(args.delay * 2)
            continue

        provider_stats[provider] = provider_stats.get(provider, 0) + 1
        new_html = inject(html, text)
        fp.write_text(new_html, "utf-8")
        progress["done"].append(name)
        save_progress(progress)
        done += 1
        print(f"OK [{provider}]")
        time.sleep(args.delay)

    print(f"\n{'='*50}")
    print(f"  Processadas : {done}")
    print(f"  Saltadas    : {skip}")
    print(f"  Erros       : {fail}")
    if provider_stats:
        print(f"  Por provider: {provider_stats}")
    print(f"{'='*50}")
    if not args.dry_run and done:
        print("\n  Proximo passo: python tools/publish.py")


if __name__ == "__main__":
    main()

