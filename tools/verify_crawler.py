import os
import glob
import re
from urllib.parse import urlparse, unquote

site_dir = r"C:\Users\SMMC\Desktop\ProjetosOrganizados\02_Automacao_DealflowBot\descontos-pt.github.io"
html_files = glob.glob(os.path.join(site_dir, "**", "*.html"), recursive=True)

# Ignorar a pasta tools
html_files = [h for h in html_files if "tools" not in h]

print(f"Auditando {len(html_files)} páginas HTML...")

broken = []
total_checked = 0

for hf in html_files:
    rel_src = os.path.relpath(hf, site_dir)
    dir_src = os.path.dirname(hf)
    with open(hf, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    # Remover o conteúdo de <script> e <style> para auditar apenas a marcação HTML pura
    clean_html = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html, flags=re.IGNORECASE)
    clean_html = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', clean_html, flags=re.IGNORECASE)

    # Capturar todas as tags <a> e <link>
    links = re.findall(r'href=["\']([^"\']+)["\']', clean_html)

    for href in links:
        total_checked += 1
        # Ignorar âncoras, javascript, mailto, tel
        if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
            continue

        # Se for link externo completo (http/https)
        if href.startswith("http://") or href.startswith("https://"):
            if "descontos-pt.github.io" in href:
                # É link absoluto para o próprio domínio
                parsed = urlparse(href)
                path = unquote(parsed.path).lstrip("/")
                if not path or path.endswith("/"):
                    target = os.path.join(site_dir, path, "index.html")
                else:
                    target = os.path.join(site_dir, path)
                    if not os.path.exists(target) and not os.path.exists(target + ".html"):
                        target = os.path.join(site_dir, path, "index.html")

                if not os.path.exists(target) and not os.path.exists(target + ".html"):
                    broken.append((rel_src, href, target, "Domínio Interno Absoluto"))
            continue

        # Link relativo
        clean_hr = unquote(href.split("?")[0].split("#")[0])
        if not clean_hr:
            broken.append((rel_src, href, "", "Link Vazio"))
            continue

        if clean_hr.startswith("/"):
            target = os.path.join(site_dir, clean_hr.lstrip("/"))
        else:
            target = os.path.join(dir_src, clean_hr)

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
            broken.append((rel_src, href, target_file, "Ficheiro Inexistente"))

print(f"\nTotal de links HTML verificados: {total_checked}")
print(f"Total de links quebrados (404) encontrados: {len(broken)}")

for src, href, tgt, reason in broken:
    print(f"  [404: {reason}] Em '{src}' -> href='{href}' (alvo: {tgt})")
