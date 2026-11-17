"""
cargar_seleccion_catalogo.py — Sube la planilla de curaduría a `catalogo_web`.

Lee curaduria/catalogo_web_seleccion.xlsx (la genera generar_planilla_curaduria.py):
  * Filas con "S" en Publicar → publicadas, con categoría, subcategoría,
    nombre web, URL de imagen y destacado tal como están en la planilla.
  * Productos que estaban publicados y en la planilla ya no tienen "S" →
    se despublican (no se borran: conservan sus datos).
No toca `descripcion` ni `orden` (no están en la planilla).
Mientras no exista el panel de administración, la planilla es la fuente de verdad.

Uso:
    python cargar_seleccion_catalogo.py --dry-run     # muestra qué haría
    python cargar_seleccion_catalogo.py
    python cargar_seleccion_catalogo.py --excel otra_ruta.xlsx

Requiere .env con SUPABASE_URL y SUPABASE_KEY (sb_secret_) y las migraciones
de supabase/migrations/ aplicadas (incluida la 20261118000003).
"""
import argparse
import collections
import json
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from openpyxl import load_workbook

AQUI = Path(__file__).parent
EXCEL_DEFECTO = AQUI / "curaduria" / "catalogo_web_seleccion.xlsx"
CATEGORIAS = {"Iluminación", "Llaves y tomas", "Cables", "Cajas y tableros",
              "Cañerías y accesorios", "Protecciones", "Otros"}
LOTE = 500


def texto(v) -> str | None:
    s = str(v).strip() if v is not None else ""
    return s or None


def leer_planilla(ruta: Path) -> tuple[list[dict], set[int], list[str]]:
    """Devuelve (filas a publicar, códigos presentes en la planilla, avisos)."""
    wb = load_workbook(ruta, read_only=True, data_only=True)
    if "Productos" not in wb.sheetnames:
        sys.exit(f"{ruta.name} no tiene la hoja 'Productos'. ¿Es la planilla de generar_planilla_curaduria.py?")
    filas = wb["Productos"].iter_rows(values_only=True)
    cab = [str(c).strip() if c else "" for c in next(filas)]
    publicar, presentes, avisos = [], set(), []
    for r in filas:
        d = dict(zip(cab, r))
        if d.get("Código") is None:
            continue
        codigo = int(d["Código"])
        presentes.add(codigo)
        if (texto(d.get("Publicar (S/N)")) or "").upper() != "S":
            continue
        cat = texto(d.get("Categoría"))
        if cat not in CATEGORIAS:
            avisos.append(f"{codigo}: categoría '{cat}' no válida → 'Otros'")
            cat = "Otros"
        url = texto(d.get("URL imagen"))
        if url and not re.match(r"^https://", url):
            avisos.append(f"{codigo}: la URL de imagen no empieza con https:// → se ignora")
            url = None
        publicar.append({
            "codigo": codigo,
            "publicado": True,
            "categoria_web": cat,
            "subcategoria_web": texto(d.get("Subcategoría")),
            "nombre_web": texto(d.get("Nombre web (opcional)")),
            "imagen_url": url,
            "destacado": (texto(d.get("Destacado (S)")) or "").upper() == "S",
        })
    wb.close()
    return publicar, presentes, avisos


def main() -> int:
    ap = argparse.ArgumentParser(description="Sube la planilla de curaduría a catalogo_web.")
    ap.add_argument("--excel", type=Path, default=EXCEL_DEFECTO)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.excel.exists():
        sys.exit(f"No existe {args.excel}. Generala con: python generar_planilla_curaduria.py")

    publicar, presentes, avisos = leer_planilla(args.excel)
    for a in avisos:
        print("  AVISO", a)

    load_dotenv(AQUI / ".env")
    url, key = os.getenv("SUPABASE_URL", "").rstrip("/"), os.getenv("SUPABASE_KEY", "")
    if not url or not key or key.startswith("sb_publishable_"):
        sys.exit("SUPABASE_KEY en .env debe ser la sb_secret_.")
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    r = requests.get(f"{url}/rest/v1/catalogo_web?select=codigo&publicado=eq.true", headers=h, timeout=60)
    r.raise_for_status()
    ya_publicados = {x["codigo"] for x in r.json()}
    marcados = {f["codigo"] for f in publicar}
    despublicar = sorted((ya_publicados & presentes) - marcados)

    por_cat = collections.Counter(f["categoria_web"] for f in publicar)
    con_foto = sum(1 for f in publicar if f["imagen_url"])
    print(f"A publicar: {len(publicar)} ({len(marcados - ya_publicados)} nuevos), con foto: {con_foto}")
    for cat, n in por_cat.most_common():
        print(f"  {n:5}  {cat}")
    print(f"A despublicar: {len(despublicar)}")

    if args.dry_run:
        print("[DRY-RUN] No se escribió nada.")
        return 0

    for i in range(0, len(publicar), LOTE):
        r = requests.post(
            f"{url}/rest/v1/catalogo_web?on_conflict=codigo",
            headers={**h, "Prefer": "resolution=merge-duplicates,return=minimal"},
            data=json.dumps(publicar[i:i + LOTE]), timeout=60)
        if r.status_code not in (200, 201, 204):
            if "subcategoria_web" in r.text or "imagen_url" in r.text:
                print("Falta aplicar la migración supabase/migrations/20261118000003_catalogo_web_fase1.sql")
            print(f"ERROR {r.status_code}: {r.text[:300]}")
            return 1

    for i in range(0, len(despublicar), LOTE):
        cods = ",".join(map(str, despublicar[i:i + LOTE]))
        r = requests.patch(f"{url}/rest/v1/catalogo_web?codigo=in.({cods})",
                           headers={**h, "Prefer": "return=minimal"},
                           data=json.dumps({"publicado": False}), timeout=60)
        if r.status_code not in (200, 204):
            print(f"ERROR al despublicar {r.status_code}: {r.text[:300]}")
            return 1

    print(f"Listo: {len(publicar)} publicados, {len(despublicar)} despublicados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
