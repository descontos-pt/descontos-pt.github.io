import os
import glob
import re
from urllib.parse import urlparse

site_dir = r"C:\Users\SMMC\Desktop\ProjetosOrganizados\02_Automacao_DealflowBot\descontos-pt.github.io"
html_files = glob.glob(os.path.join(site_dir, "**", "*.html"), recursive=True)

print(f"A verificar {len(html_files)} ficheiros HTML...")

malformed_links = []
internal_404s = []
empty_links = []

for hf in html_files:
    rel_path = os.path.relpath(hf, site_dir)
    dir_of_file = os.path.dirname(hf)
    with open(hf, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Extrair todos os hrefs
    hrefs = re.findall(r'href=["\']([^"\']*)["\']', content)
    for hr in hrefs:
        if hr == "" or hr == "undefined" or hr == "null":
            empty_links.append((rel_path, hr))
            continue

        if hr.startswith("#") or hr.startswith("javascript:") or hr.startswith("mailto:") or hr.startswith("tel:"):
            continue

        # Verificar se é link relativo interno
        if not hr.startswith("http://") and not hr.startswith("https://"):
            clean_hr = hr.split("?")[0].split("#")[0]
            if clean_hr.startswith("/"):
                target = os.path.join(site_dir, clean_hr.lstrip("/"))
            else:
                target = os.path.join(dir_of_file, clean_hr)
            
            target = os.path.normpath(target)
            if os.path.isdir(target):
                target_file = os.path.join(target, "index.html")
            elif not os.path.exists(target):
                if os.path.exists(target + ".html"):
                    target_file = target + ".html"
                elif os.path.exists(os.path.join(target, "index.html")):
                    target_file = os.path.join(target, "index.html")
                else:
                    target_file = target
            else:
                target_file = target

            if not os.path.exists(target_file):
                internal_404s.append((rel_path, hr, target_file))

        # Verificar URLs de afiliados externas
        elif "amazon" in hr or "aliexpress" in hr or "awin1" in hr:
            if "undefined" in hr or "null" in hr:
                malformed_links.append((rel_path, hr))

print("\n=== RESULTADOS DA AUDITORIA DE LINKS ===")
print(f"Links vazios / indefinidos (href='' ou href='undefined'): {len(empty_links)}")
for src, hr in empty_links[:20]:
    print(f"  [Vazio/Undefined] Em {src}: href='{hr}'")

print(f"\nLinks Internos 404: {len(internal_404s)}")
for src, hr, tgt in internal_404s[:20]:
    print(f"  [404 Interno] Em {src} -> href='{hr}'")

print(f"\nLinks Externos Malformados: {len(malformed_links)}")
for src, hr in malformed_links[:20]:
    print(f"  [Externo Malformado] Em {src} -> href='{hr}'")
