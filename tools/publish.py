#!/usr/bin/env python3
"""
publish.py
==========
Faz add + commit + push de todas as alteracoes para o GitHub.
Executa depois de enrich_products.py e/ou convert_redirects.py.

Uso:
    python tools/publish.py
    python tools/publish.py --message "Mensagem de commit personalizada"
"""

import subprocess
import sys
import argparse
from datetime import datetime

def run(cmd, check=True):
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if check and result.returncode != 0:
        print(f"ERRO (codigo {result.returncode})")
        sys.exit(1)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", default="", help="Mensagem de commit")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ts  = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = args.message or f"[auto] Enriquecimento de paginas de produto com IA ({ts})"

    print("\n=== PUBLICAR PARA GITHUB ===\n")

    # Verificar o que mudou
    status = run(["git", "status", "--short"], check=False)
    changed = status.stdout.strip()
    if not changed:
        print("Nenhuma alteracao encontrada. Tudo ja esta atualizado.")
        return

    lines = changed.splitlines()
    print(f"\nFicheiros alterados: {len(lines)}")
    for l in lines[:10]:
        print(f"  {l}")
    if len(lines) > 10:
        print(f"  ... e mais {len(lines)-10}")

    if args.dry_run:
        print("\n[dry-run] Nao foi feito push.")
        return

    print("\n--- git add ---")
    run(["git", "add", "-A"])

    print("\n--- git commit ---")
    run(["git", "commit", "-m", msg])

    print("\n--- git push ---")
    run(["git", "push"])

    print("\n✅ Publicado com sucesso!")
    print("   O site estara atualizado em 1-2 minutos no GitHub Pages.")


if __name__ == "__main__":
    main()
