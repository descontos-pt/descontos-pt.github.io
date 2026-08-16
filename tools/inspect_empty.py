import re

with open(r"C:\Users\SMMC\Desktop\ProjetosOrganizados\02_Automacao_DealflowBot\descontos-pt.github.io\index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    m = re.findall(r'href=["\']([^"\']*)["\']', line)
    for h in m:
        if h == "" or h == "undefined" or h == "null":
            print(f"Linha {idx+1}: {line.strip()}")
