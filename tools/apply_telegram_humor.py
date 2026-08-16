import sys, os, re, hashlib
from pathlib import Path
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).parent.parent
DEALS_DIR = REPO_ROOT / "d"
REDIRECTS_DIR = REPO_ROOT / "r"

# ── Regras de Humor e Ganchos por Tipo de Produto (Base Telegram) ──────────────
PRODUCT_RULES = [
    (r"smartphone|telem[oó]vel|iphone|galaxy\s+s\d|galaxy\s+a\d|redmi|xiaomi\s+\d|poco\s+|pixel\s+\d|oneplus|realme|honor\s+\d", [
        ("Eu mereço o melhor 🏆", "Tão rápido que envia a mensagem antes de a acabares de pensar. 📱", "Perfeito para quem quer fotos nítidas e bateria para o dia todo."),
        ("O upgrade que andavas a adiar ⚡", "O teu telemóvel atual viu este e pediu a reforma antecipada. 📴", "Ecrã super fluido que torna o scroll e as redes sociais um vício."),
        ("Bateria de maratona 🔋", "Bateria que aguenta mais do que as tuas promessas de Ano Novo.", "Mais armazenamento para todas as fotos e vídeos que nunca vais apagar."),
    ]),
    (r"port[áa]til|laptop|notebook|macbook|chromebook|computador", [
        ("Produtividade sem limites 💼", "Tão rápido que o Excel abre antes de mudares de ideias. ⚡", "O teu chefe vai jurar que ficaste 50% mais produtivo no trabalho."),
        ("Máquina para tudo 🚀", "RAM de sobra para 50 separadores abertos e jogar entre reuniões.", "O portátil que finalmente não te queima as pernas nas videochamadas."),
    ]),
    (r"auricular|headphone|earphone|airpods|earbuds|fones|soundcore|cancelamento.*ru[ií]do", [
        ("Silêncio e som puro 🎧", "Cancelamento de ruído tão bom que nem os vizinhos do andar de cima ouves. 🤫", "Silêncio seletivo: ouves a tua música favorita e esqueces o barulho à volta."),
        ("Som de concerto 🎶", "Vão fazer-te gostar de músicas que juravas detestar.", "Chamadas de trabalho cristalinas e bateria para dias inteiros de uso."),
    ]),
    (r"smartwatch|apple\s*watch|galaxy\s*watch|rel[óo]gio.*inteligente|amazfit|garmin|fitbit", [
        ("Saúde e estilo no pulso ⌚", "Conta os teus passos e julga o teu sedentarismo em silêncio. Justamente.", "Notificações no pulso para ignorares reuniões com muito mais estilo. 🏃"),
        ("Treino levado a sério 🏃", "O personal trainer que cabe no pulso e nunca tira folga.", "Mede o sono, passos e ritmo cardíaco com precisão máxima."),
    ]),
    (r"sapatilha|t[ée]nis|sapatos|sneaker|adidas|nike|puma|asics|new\s*balance|vans|crocs", [
        ("Estilo nos pés, conforto no dia a dia 👟", "Amortecimento que faz a calçada portuguesa parecer alcatifa macia. 🏃", "Perfeitas para caminhadas, ginásio ou um look descontraído com estilo."),
        ("Eu mereço o melhor 🏆", "Tão confortáveis que vais inventar desculpas para ir a pé para todo o lado.", "O calçado versátil que combina com tudo e não cansa ao fim de horas."),
    ]),
    (r"casaco|t-shirt|cal[çc][õa]|polo|camisa|vestido|cueca|suti[ãa]|roupa|g-star|tommy|levis|calvin\s*klein", [
        ("Visual impecável ✨", "Corte moderno que assenta na perfeição e dura muito além de uma estação. 👕", "O básico de marca com acabamento premium que valoriza qualquer look diário."),
        ("Renovação de armário 👌", "Qualidade de tecido superior que não perde a forma após as lavagens.", "Aquele artigo essencial que vais usar vezes sem conta sem te cansares."),
    ]),
    (r"aspirador|robot.*aspirador|roomba|dreame|roborock|vassoura.*aspirador|vactech", [
        ("Casa limpa sem esforço 🧹", "Limpa a casa toda sem reclamar — devia ser o padrão em todas as divisões. 🏠", "Poder de sucção que encontra pó onde tu nem sabias que existia."),
        ("A automação que precisavas ✨", "A tua casa limpa e aspirada enquanto ficas no sofá a relaxar. 🛋️", "A tarefa doméstica mais aborrecida da semana acaba de ficar resolvida."),
    ]),
    (r"c[âa]mara|videovigil[âa]ncia|blink|ring|tapo|intercom|campainha", [
        ("Segurança e tranquilidade 📹", "Espreita quem está à porta mesmo quando estás a quilómetros de distância. 🔔", "Vê se as encomendas chegaram em segurança com imagem nítida dia e noite."),
    ]),
    (r"creme|s[ée]rum|facial|beleza|cerave|foreo|perfume|maquilhagem|l'oreal|escova.*dentes|oral-b", [
        ("Cuidado diário de topo ✨", "Rotina de cuidados com resultados visíveis no espelho logo nos primeiros dias. 💆", "Qualidade profissional de dermatologia e cuidado pessoal em tua casa."),
    ]),
    (r"lego|brinquedo|bonec|pinypon|barbie|vatos|jogo.*tabuleiro|puzzle", [
        ("Diversão garantida 🧩", "Horas de entretenimento garantido longe dos ecrãs e telemóveis. 🎁", "O presente perfeito para estimular a criatividade dos mais novos."),
    ]),
]

FALLBACK_TRIPLET = ("Excelente oportunidade 🔥", "Um produto com excelente reputação e procura comprovada. 👌", "Combina materiais resistentes com grande utilidade para o dia a dia.")

def get_product_triplet(title: str):
    t = title.lower()
    for pattern, triplets in PRODUCT_RULES:
        if re.search(pattern, t):
            idx = int(hashlib.md5(title.encode('utf-8')).hexdigest(), 16) % len(triplets)
            return triplets[idx]
    return FALLBACK_TRIPLET

def extract_deal_info(soup, html_text):
    title = ""
    t = soup.find("title")
    if t:
        title = re.sub(r"\s*por\s+[\d,.]+\s*[\u20ac€].*$", "", t.get_text(), flags=re.I)
        title = re.sub(r"\s*[\|–-].*$", "", title).strip()
    if not title:
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else "Produto em promoção"

    price = old_price = discount = ""
    for cls in ["bignew", "new-price", "price-new", "new"]:
        el = soup.find(class_=cls)
        if el: price = el.get_text(strip=True); break

    for cls in ["bigold", "old-price", "price-old", "old"]:
        el = soup.find(class_=cls)
        if el: old_price = el.get_text(strip=True); break

    for cls in ["bigsave", "savings", "disc", "badge"]:
        el = soup.find(class_=cls)
        if el and "%" in el.get_text():
            m = re.search(r"(\d+%)", el.get_text())
            if m: discount = m.group(1); break

    store = "Amazon"
    if "aliexpress" in html_text.lower(): store = "AliExpress"
    elif "awin" in html_text.lower(): store = "Parceiro Oficial"

    return title, price, old_price, discount, store

def build_telegram_style_editorial(title, price, old_price, discount, store):
    badge, hook, detail = get_product_triplet(title)
    
    disc_text = f" com <strong>{discount} de desconto</strong>" if discount else ""
    price_text = f"desce de {old_price} para apenas <strong>{price}</strong>" if (old_price and price) else f"está disponível por <strong>{price or 'ótimo preço'}</strong>"

    return f"""<p style="margin-bottom:8px;"><strong>🔥 {badge}</strong></p>
<p style="margin-bottom:8px;">{hook} {detail}</p>
<p style="margin-bottom:8px;">💰 Na {store}, o valor {disc_text} {price_text}, representando uma oportunidade muito atrativa face ao preço habitual de mercado.</p>
<p style="color:var(--muted,#64748b);font-size:13.5px;">👀 <em>Já viste, já sabes — a estes valores o stock costuma voar rápido. Confirma o preço atual antes de comprar.</em></p>"""

def process_directory(dir_path):
    count = 0
    for fp in sorted(dir_path.glob("**/*.html")):
        if "index.html" not in fp.name and dir_path.name == "r":
            continue
        try:
            html = fp.read_text("utf-8", errors="replace")
            soup = BeautifulSoup(html, "html.parser")
            
            title, price, old_price, discount, store = extract_deal_info(soup, html)
            new_editorial = build_telegram_style_editorial(title, price, old_price, discount, store)
            
            # Substituir no bloco editorial
            if "editorial-desc" in html:
                html = re.sub(
                    r'(<div class="editorial-desc">)(.*?)(</div>)',
                    lambda m: f'{m.group(1)}\n        {new_editorial}\n      {m.group(3)}',
                    html,
                    flags=re.DOTALL
                )
            elif 'class="editorial"' in html:
                html = re.sub(
                    r'(<div class="editorial">)(.*?)(</div>)',
                    lambda m: f'{m.group(1)}\n        {new_editorial}\n      {m.group(3)}',
                    html,
                    flags=re.DOTALL
                )
            else:
                block = f'\n    <div class="panel editorial-panel">\n      <div class="editorial-desc">\n        {new_editorial}\n      </div>\n    </div>\n'
                if '<div class="panel">' in html:
                    html = html.replace('<div class="panel">', block + '    <div class="panel">', 1)
                else:
                    html = html.replace('</body>', block + '</body>', 1)

            fp.write_text(html, "utf-8")
            count += 1
        except Exception as e:
            print(f"Erro em {fp.name}: {e}")
            
    return count

print("=== ENRIQUECENDO CONTEÚDOS COM O FORMATO COMPLETO DO TELEGRAM ===")
d_count = process_directory(DEALS_DIR)
r_count = process_directory(REDIRECTS_DIR)
print(f"Sucesso: {d_count} páginas em /d/ e {r_count} páginas em /r/ enriquecidas!")
