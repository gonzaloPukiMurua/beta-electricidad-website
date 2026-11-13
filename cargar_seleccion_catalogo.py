"""
cargar_seleccion_catalogo.py — Carga la selección curada en `catalogo_web`.

Lee el Excel de curaduría (columna "Incluir (S/N)") y marca como publicados
en `catalogo_web` los códigos con "S", con su categoría web.
Solo escribe las columnas codigo, publicado y categoria_web: no pisa nombres,
descripciones ni el orden que se carguen después desde el admin.

Uso:
    python cargar_seleccion_catalogo.py --dry-run
    python cargar_seleccion_catalogo.py
    python cargar_seleccion_catalogo.py --excel otra_ruta.xlsx

Requiere .env en esta carpeta con SUPABASE_URL y SUPABASE_KEY (service_role),
igual que sincronizar_db.py. Requiere haber corrido las migraciones de
supabase/migrations/.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

import openpyxl
import openpyxl.reader.excel as _rx

# Algunos Excel guardados por otras apps traen estilos que openpyxl no entiende;
# no los necesitamos para leer valores.
_rx.apply_stylesheet = lambda archive, wb: None

AQUI = Path(__file__).parent
EXCEL_DEFECTO = AQUI / "curaduria" / "top200_iluminacion_llaves.xlsx"
HOJAS = ("Top 200", "Resto con ventas")


def leer_seleccion(ruta: Path) -> list[dict]:
    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    filas = []
    for hoja in HOJAS:
        if hoja not in wb.sheetnames:
            continue
        rows = list(wb[hoja].iter_rows(values_only=True))
        if not rows:
            continue
        h = [str(c).strip() if c is not None else "" for c in rows[0]]
        try:
            i_cod, i_inc, i_cat = h.index("Código"), h.index("Incluir (S/N)"), h.index("Categoría web")
        except ValueError:
            print(f"  (hoja '{hoja}' sin columnas Código / Incluir (S/N) / Categoría web: se omite)")
            continue
        for r in rows[1:]:
            if r[i_inc] and str(r[i_inc]).strip().upper() == "S" and r[i_cod] is not None:
                filas.append({
                    "codigo": int(str(r[i_cod]).strip()),
                    "publicado": True,
                    "categoria_web": (str(r[i_cat]).strip() if r[i_cat] else None),
                })
    wb.close()
    # sin duplicados (si un código está en las dos hojas, queda el primero)
    vistos, unicos = set(), []
    for f in filas:
        if f["codigo"] not in vistos:
            vistos.add(f["codigo"])
            unicos.append(f)
    return unicos


def main() -> int:
    ap = argparse.ArgumentParser(description="Carga la selección curada en catalogo_web.")
    ap.add_argument("--excel", type=Path, default=EXCEL_DEFECTO)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    filas = leer_seleccion(args.excel)
    print(f"Productos marcados con S: {len(filas)}")
    if not filas:
        return 0
    if args.dry_run:
        print("[DRY-RUN] Ejemplo:", json.dumps(filas[:3], ensure_ascii=False))
        return 0

    load_dotenv(AQUI / ".env")
    url, key = os.getenv("SUPABASE_URL", "").rstrip("/"), os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        sys.exit("Falta SUPABASE_URL o SUPABASE_KEY en .env")

    resp = requests.post(
        f"{url}/rest/v1/catalogo_web?on_conflict=codigo",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        data=json.dumps(filas),
        timeout=30,
    )
    if resp.status_code not in (200, 201, 204):
        print(f"ERROR {resp.status_code}: {resp.text[:300]}")
        return 1
    print(f"Listo: {len(filas)} productos publicados en catalogo_web.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
