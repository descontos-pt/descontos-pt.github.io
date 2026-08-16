import sys, os, re, hashlib
from pathlib import Path
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).parent.parent
DEALS_DIR = REPO_ROOT / "d"
REDIRECTS_DIR = REPO_ROOT / "r"

# ── Dicionário de tradução rápida Espanhol → Português para títulos ───────────
ES_TO_PT = [
    (r"\bZapatos Hombre\b", "Sapatilhas Homem"),
    (r"\bZapatos Mujer\b", "Sapatilhas Mulher"),
    (r"\bZapatillas\b", "Sapatilhas"),
    (r"\bCamiseta de manga corta\b", "T-Shirt de manga curta"),
    (r"\bCamiseta\b", "T-Shirt"),
    (r"\bPantalones\b", "Calças"),
    (r"\bChaqueta\b", "Casaco"),
    (r"\bSudadera\b", "Sweatshirt"),
    (r"\bReloj de Cuarzo\b", "Relógio de Quartzo"),
    (r"\bReloj\b", "Relógio"),
    (r"\bCámara\b", "Câmara"),
    (r"\bCepillo de Dientes Eléctrico\b", "Escova de Dentes Elétrica"),
    (r"\bAuriculares inalámbricos\b", "Auriculares sem fios"),
]

def clean_title_pt(t: str) -> str:
    res = t
    for es, pt in ES_TO_PT:
        res = re.sub(es, pt, res, flags=re.I)
    return res

# ── Extrator Inteligente de Especificações e Destaques Técnicos ──────────────
def extract_specs_list(title: str, cat: str = ""):
    t = title.lower()
    specs = []

    # 1. COMPUTADORES / PORTÁTEIS / PCS
    if re.search(r"port[áa]til|laptop|notebook|macbook|chromebook|computador|ideapad|thinkpad|inspiron|pavilion|zenbook|vivobook|pc\b", t):
        m_cpu = re.search(r"(ryzen\s*\d\s*\w*|core\s*i[3579]\s*[\w-]*|intel\s*n\d+|apple\s*m\d|snapdragon\s*x)", t)
        cpu = f"Processador {m_cpu.group(1).upper()} para arranque rápido e fluidez multitarefa" if m_cpu else "Processador de alto desempenho otimizado para produtividade e eficiência energética"
        specs.append(("Processador", cpu))

        ram_ssd = []
        m_ram = re.search(r"(\d+\s*gb\s*ram|\d+\s*gb\s*ddr\d?)", t)
        if m_ram: ram_ssd.append(m_ram.group(1).upper())
        m_ssd = re.search(r"(\d+\s*(?:gb|tb)\s*ssd|\d+\s*(?:gb|tb)\s*nvme)", t)
        if m_ssd: ram_ssd.append(m_ssd.group(1).upper())
        specs.append(("Memória & Armazenamento", f"Configuração com {' + '.join(ram_ssd)} para abertura instantânea de ficheiros e multitarefa ágil" if ram_ssd else "Armazenamento em SSD veloz e memória RAM fluida para arranque em poucos segundos"))

        m_scr = re.search(r'(\d+[\.,]?\d*["\']|\d+[\.,]?\d*\s*polegadas)', t)
        specs.append(("Ecrã & Resolução", f"Painel de {m_scr.group(1)} com tratamento antirreflexo para maior conforto visual" if m_scr else "Ecrã de alta definição com cores calibradas para trabalho prolongado e entretenimento"))
        specs.append(("Conetividade & Autonomia", "Portas USB-C, Wi-Fi rápido e bateria dimensionada para acompanharem o dia"))

    # 2. SMARTPHONES & TABLETS
    elif re.search(r"smartphone|telem[oó]vel|iphone|galaxy\s+s\d|galaxy\s+a\d|redmi|xiaomi\s+\d|poco|pixel\s+\d|oneplus|realme|honor|tablet|ipad", t):
        m_hz = re.search(r"(\d+hz|amoled|oled|fhd\+?)", t)
        specs.append(("Ecrã", f"Painel {m_hz.group(1).upper()} com taxa de atualização fluida e excelente visibilidade sob luz solar" if m_hz else "Painel táctil de alta resolução com cores vibrantes e grande fidelidade cromática"))

        m_cam = re.search(r"(\d+\s*mp|\d+\s*megapixels?)", t)
        specs.append(("Câmara & Fotografia", f"Sensor principal de {m_cam.group(1).upper()} com assistência por IA para imagens ricas em detalhe" if m_cam else "Sistema de câmara com processamento inteligente para fotografias nítidas dia e noite"))

        m_bat = re.search(r"(\d{4}\s*mah|\d+\s*w)", t)
        specs.append(("Bateria & Carregamento", f"Bateria de {m_bat.group(1).upper()} com suporte a carregamento rápido para maior independência da tomada" if m_bat else "Bateria de longa duração dimensionada para utilização intensiva de manhã à noite"))

        m_cap = re.search(r"(\d+\s*gb|\d+\s*tb)", t)
        if m_cap:
            specs.append(("Armazenamento Interno", f"{m_cap.group(1).upper()} de capacidade para armazenar aplicações, fotografias e conteúdos multimédia"))

    # 3. AURICULARES & SOM
    elif re.search(r"auricular|headphone|earphone|airpods|earbuds|fones|soundcore|coluna|soundbar|bluetooth", t):
        specs.append(("Qualidade Acústica", "Drivers de som afinados para equilíbrio tonal preciso, com agudos nítidos e graves envolventes"))
        if re.search(r"anc|cancelamento|ru[ií]do", t):
            specs.append(("Cancelamento de Ruído (ANC)", "Tecnologia ativa de redução de ruído para isolamento imersivo em viagens e escritórios"))
        else:
            specs.append(("Isolamento Acústico", "Formato ergonómico com isolamento passivo eficaz contra o ruído ambiente"))
        specs.append(("Autonomia & Chamadas", "Bateria duradoura combinada com o estojo de carga e microfone com cancelamento de eco"))

    # 4. CALÇADO & SAPATILHAS
    elif re.search(r"sapatilha|t[ée]nis|sapatos|sneaker|adidas|nike|puma|asics|new\s*balance|vans|crocs|bota", t):
        m_tech = re.search(r"(cloudfoam|boost|air\s*max|react|eva|memory\s*foam|gore-tex|ortholite)", t)
        tech_str = f"Tecnologia {m_tech.group(1).title()}" if m_tech else "Entressola com amortecimento absorvente"
        specs.append(("Amortecimento & Sola", f"{tech_str} que minimiza o impacto articular e assegura conforto duradouro"))
        specs.append(("Material & Tecido", "Estrutura exterior em malha têxtil respirável e materiais flexíveis que se ajustam ao contorno do pé"))
        specs.append(("Aderência & Tração", "Sola exterior de borracha resistente com padrão antiderrapante para segurança em vários tipos de piso"))
        specs.append(("Ergonomia", "Corte envolvente que equilibra firmeza no calcanhar com liberdade natural nos dedos"))

    # 5. ROUPA & VESTUÁRIO
    elif re.search(r"casaco|t-shirt|cal[çc][õa]|polo|camisa|vestido|cueca|suti[ãa]|roupa|g-star|tommy|levis|calvin\s*klein|blus[ãa]o|parka", t):
        specs.append(("Composição & Toque", "Tecido respirável de toque suave e estrutura de malha densa que garante conforto térmico equilibrado"))
        specs.append(("Corte & Caimento", "Design ergonómico desenhado para proporcionar liberdade de movimentos e uma silhueta elegante"))
        specs.append(("Resistência & Durabilidade", "Costuras reforçadas que mantêm a integridade da peça e a estabilidade das cores lavagem após lavagem"))
        specs.append(("Versatilidade", "Peça prática e intemporal, fácil de combinar em estilos casuais ou mais compostos"))

    # 6. SMARTWATCHES & WEARABLES
    elif re.search(r"smartwatch|apple\s*watch|galaxy\s*watch|rel[óo]gio.*inteligente|amazfit|garmin|fitbit", t):
        specs.append(("Monitorização de Saúde", "Sensores biométricos para medição de frequência cardíaca, oxigénio no sangue (SpO2) e análise de sono"))
        specs.append(("Modos de Treino", "Registo automático de atividades desportivas com contagem de passos, calorias e métricas de desempenho"))
        specs.append(("Conetividade & Notificações", "Sincronização imediata de alertas de chamadas, mensagens e aplicações diretamente no pulso"))
        specs.append(("Autonomia & Resistência", "Bateria de longa duração e estrutura resistente a salpicos e poeiras"))

    # 7. ELETRODOMÉSTICOS & CASA
    elif re.search(r"aspirador|robot|dreame|roborock|air\s*fryer|fritadeira|cafeteira|m[áa]quina|ferro|liquidificador|micro-ondas|ventilador", t):
        m_pot = re.search(r"(\d+\s*w|\d+\s*pa|\d+[\.,]?\d*\s*l\b)", t)
        specs.append(("Potência & Eficiência", f"Capacidade/Potência de {m_pot.group(1).upper()} para resultados rápidos com consumo energético controlado" if m_pot else "Motor de alto rendimento otimizado para máxima eficácia com baixo consumo"))
        specs.append(("Praticidade & Limpeza", "Acessórios e reservatórios destacáveis de fácil higienização e manutenção"))
        specs.append(("Construção & Segurança", "Materiais duradouros de qualidade alimentar e sistemas integrados de proteção térmica"))

    # 8. CÂMARAS & SEGURANÇA
    elif re.search(r"c[âa]mara|videovigil[âa]ncia|blink|ring|tapo|intercom|campainha|vigil[âa]ncia", t):
        specs.append(("Qualidade de Imagem", "Resolução nítida com visão noturna por infravermelhos para vigilância detalhada 24 horas por dia"))
        specs.append(("Deteção & Alertas", "Sensores de movimento com envio instantâneo de notificações para o smartphone"))
        specs.append(("Áudio & Resistência", "Comunicação de áudio bidirecional (microfone e altifalante) e corpo resistente a intempéries exteriores"))

    # 9. DEFAULT / OUTROS PRODUTOS
    else:
        specs.append(("Qualidade de Fabrico", "Construção robusta com acabamento resistente concebido para utilização frequente e fiável"))
        specs.append(("Funcionalidade & Ergonomia", "Design prático e intuitivo focado em proporcionar comodidade e utilidade no dia a dia"))
        specs.append(("Garantia & Fiabilidade", "Em conformidade com os exigentes padrões europeus de segurança e qualidade"))

    return specs

# ── Regras de Humor e Ganchos por Tipo de Produto (Base Telegram) ──────────────
PRODUCT_RULES = [
    (r"smartphone|telem[oó]vel|iphone|galaxy\s+s\d|galaxy\s+a\d|redmi|xiaomi\s+\d|poco\s+|pixel\s+\d|oneplus|realme|honor\s+\d", [
        ("Eu mereço o melhor 🏆", "Tão rápido que envia a mensagem antes de a acabares de pensar. 📱", "Perfeito para quem quer fotos nítidas e bateria para o dia todo."),
        ("O upgrade que andavas a adiar ⚡", "O teu telemóvel atual viu este e pediu a reforma antecipada. 📴", "Ecrã super fluido que torna o scroll e as redes sociais um vício."),
        ("Bateria de maratona 🔋", "Bateria que aguenta mais do que as tuas promessas de Ano Novo.", "Mais armazenamento para todas as fotos e vídeos que nunca vais apagar."),
    ]),
    (r"port[áa]til|laptop|notebook|macbook|chromebook|computador|ideapad|thinkpad", [
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

    title = clean_title_pt(title)

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

    # DETECÇÃO PRECISA DA LOJA
    store = "Amazon"
    btn = soup.find("a", class_=re.compile(r"buybtn|btn", re.I))
    href = btn.get("href", "").lower() if btn else ""
    btn_text = btn.get_text().lower() if btn else ""

    if "aliexpress" in href or "aliexpress" in btn_text:
        store = "AliExpress"
    elif "worten" in href or "worten" in btn_text:
        store = "Worten"
    elif "pccomponentes" in href or "pccomponentes" in btn_text:
        store = "PcComponentes"
    elif "leroymerlin" in href or "leroy" in btn_text:
        store = "Leroy Merlin"
    elif "awin" in href:
        store = "Parceiro Oficial"
    elif "amazon" in href or "amazon" in btn_text:
        store = "Amazon"

    return title, price, old_price, discount, store

def build_telegram_style_editorial(title, price, old_price, discount, store):
    badge, hook, detail = get_product_triplet(title)
    specs = extract_specs_list(title)
    
    disc_text = f" com <strong>{discount} de desconto</strong>" if discount else ""
    price_text = f"desce de {old_price} para apenas <strong>{price}</strong>" if (old_price and price) else f"está disponível por <strong>{price or 'ótimo preço'}</strong>"

    # Construir lista de especificações em HTML
    specs_items = "\n".join([f'        <li style="margin-bottom:4px;"><strong>{k}:</strong> {v}</li>' for k, v in specs])

    return f"""<p style="margin-bottom:10px;"><strong>🔥 {badge}</strong></p>
<p style="margin-bottom:10px;">{hook} {detail}</p>

<div class="specs-box" style="background:var(--bg,#f8fafc);border:1px solid var(--line,#e2e8f0);border-radius:12px;padding:12px 16px;margin:14px 0;">
  <p style="font-weight:700;font-size:13.5px;color:var(--text,#0f172a);margin-bottom:8px;">📋 <strong>Especificações & Destaques:</strong></p>
  <ul style="margin:0;padding-left:18px;font-size:13.5px;line-height:1.65;color:var(--text,#334155);">
{specs_items}
  </ul>
</div>

<p style="margin-bottom:8px;">💰 Na {store}, o valor{disc_text} {price_text}, representando uma oportunidade muito vantajosa face ao preço de tabela.</p>
<p style="color:var(--muted,#64748b);font-size:13px;margin-top:6px;">👀 <em>Já viste, já sabes — a estes valores o stock costuma voar rápido. Confirma o preço atual antes de comprar.</em></p>"""

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

print("=== APLICANDO ESPECIFICAÇÕES TÉCNICAS E TECIDOS A TODAS AS PÁGINAS ===")
d_count = process_directory(DEALS_DIR)
r_count = process_directory(REDIRECTS_DIR)
print(f"✅ Concluído com Sucesso: {d_count} páginas em /d/ e {r_count} páginas em /r/ enriquecidas com especificações técnicas e materiais!")
