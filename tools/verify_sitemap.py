import os
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

site_dir = r"C:\Users\SMMC\Desktop\ProjetosOrganizados\02_Automacao_DealflowBot\descontos-pt.github.io"
sitemap_path = os.path.join(site_dir, "sitemap.xml")

if not os.path.exists(sitemap_path):
    print("sitemap.xml nao encontrado!")
    exit(1)

tree = ET.parse(sitemap_path)
root = tree.getroot()

namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
urls = root.findall('ns:url', namespace)

print(f"Total de URLs no sitemap.xml: {len(urls)}")

missing = []
for u in urls:
    loc = u.find('ns:loc', namespace).text
    parsed = urlparse(loc)
    path = parsed.path.lstrip('/')
    if not path:
        target = os.path.join(site_dir, 'index.html')
    elif path.endswith('/'):
        target = os.path.join(site_dir, path, 'index.html')
    else:
        target = os.path.join(site_dir, path)
        if not os.path.exists(target):
            target = os.path.join(site_dir, path, 'index.html')

    if not os.path.exists(target):
        missing.append((loc, target))

print(f"URLs no sitemap.xml com 404 (inexistentes no disco): {len(missing)}")
for loc, tgt in missing:
    print(f"  [SITEMAP 404] {loc} (procurado: {tgt})")
