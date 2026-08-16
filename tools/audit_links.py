import os
import glob
import re
from urllib.parse import urlparse

site_dir = r"C:\Users\SMMC\Desktop\ProjetosOrganizados\02_Automacao_DealflowBot\descontos-pt.github.io"
html_files = glob.glob(os.path.join(site_dir, "**", "*.html"), recursive=True)

broken_links = []
total_links = 0

for hf in html_files:
    rel_path = os.path.relpath(hf, site_dir)
    dir_of_file = os.path.dirname(hf)
    with open(hf, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Encontrar todos os hrefs
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', content)
    for href in hrefs:
        total_links += 1
        # Ignorar âncoras, javascript, mailto, tel
        if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        if href.startswith("http://") or href.startswith("https://"):
            if "descontos-pt.github.io" in href:
                parsed = urlparse(href)
                target_path = parsed.path.lstrip("/")
                if not target_path or target_path.endswith("/"):
                    target_file = os.path.join(site_dir, target_path, "index.html")
                else:
                    target_file = os.path.join(site_dir, target_path)
                if not os.path.exists(target_file) and not os.path.exists(target_file + ".html") and not os.path.exists(os.path.join(site_dir, target_path, "index.html")):
                    broken_links.append((rel_path, href, target_file))
            continue

        clean_href = href.split("?")[0].split("#")[0]
        if not clean_href:
            continue

        if clean_href.startswith("/"):
            target = os.path.join(site_dir, clean_href.lstrip("/"))
        else:
            target = os.path.join(dir_of_file, clean_href)

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
            broken_links.append((rel_path, href, target_file))

print(f"Total HTMLs analisados: {len(html_files)}")
print(f"Total Links analisados: {total_links}")
print(f"Links quebrados encontrados: {len(broken_links)}")

unique_broken = {}
for src, hr, tgt in broken_links:
    unique_broken.setdefault(hr, []).append(src)

for hr, sources in list(unique_broken.items()):
    print(f"  [404] href='{hr}' (aparece em {len(sources)} paginas: ex. {sources[0]})")
