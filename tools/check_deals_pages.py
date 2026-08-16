import os
import json
import re

site_dir = r"C:\Users\SMMC\Desktop\ProjetosOrganizados\02_Automacao_DealflowBot\descontos-pt.github.io"
d_dir = os.path.join(site_dir, "d")
r_dir = os.path.join(site_dir, "r")

existing_d = set(os.listdir(d_dir)) if os.path.exists(d_dir) else set()
existing_r = set(os.listdir(r_dir)) if os.path.exists(r_dir) else set()

index_html = os.path.join(site_dir, "index.html")
with open(index_html, "r", encoding="utf-8") as f:
    content = f.read()

m = re.search(r"const DEALS\s*=\s*(\[.*?\]);", content)
if m:
    deals = json.loads(m.group(1))
    print(f"Total deals no index.html: {len(deals)}")
    missing = []
    for d in deals:
        expected = f"{d['id']}.html"
        if expected not in existing_d:
            missing.append((d['id'], d.get('title', 'Sem titulo'), d.get('url', '')))
    print(f"Deals no index.html sem pagina em /d/: {len(missing)}")
    for did, title, url in missing:
        print(f"  [404 em /d/] ID: {did} -> {title[:60]}")
else:
    print("DEALS array nao encontrado no index.html")

# Verificar também os links de /r/
print(f"Total paginas em /d/: {len(existing_d)}")
print(f"Total paginas em /r/: {len(existing_r)}")
