"""
respaldar_supabase.py — Respaldo de los datos de Supabase (el plan gratis no incluye backups).

Guarda en respaldos/ un archivo respaldo_YYYYMMDD_HHMM.json.gz con:
  * catalogo_web, config_web, admins: lo que decide el negocio y NO sale del ERP
    (es lo importante: si se pierde, hay que volver a curar el catálogo).
  * productos: copia completa de la tabla (se puede regenerar desde el ERP, pero
    sirve para comparar o volver atrás rápido).
El esquema (tablas, vista, políticas) está en supabase/migrations/, en git.
Los usuarios de Supabase Auth no se respaldan: si hubiera que restaurar `admins`
en otro proyecto, primero se recrean los usuarios.

Uso:
    python respaldar_supabase.py                       # respaldo ahora
    python respaldar_supabase.py --si-pasaron-dias 7   # solo si el último tiene 7+ días
                                                       # (así lo llama sincronizar.bat)
    python respaldar_supabase.py --restaurar respaldos/respaldo_X.json.gz --tabla catalogo_web
    python respaldar_supabase.py --restaurar respaldos/respaldo_X.json.gz --tabla catalogo_web --dry-run

Requiere .env con SUPABASE_URL y SUPABASE_KEY (sb_secret_), igual que sincronizar_db.py.
Los respaldos contienen costos y listas de precio: la carpeta respaldos/ está
en .gitignore y no se sube al repo (que es público).
"""
import argparse
import gzip
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

AQUI = Path(__file__).parent
CARPETA = AQUI / "respaldos"
# tabla -> columna para paginar en orden estable
TABLAS = {"catalogo_web": "codigo", "config_web": "id", "admins": "user_id", "productos": "codigo"}
# Restaurables: productos sale del ERP (se regenera con la sincronización) y
# admins depende de los ids de Supabase Auth.
RESTAURABLES = {"catalogo_web": "codigo", "config_web": "id"}
CONSERVAR = 12          # respaldos que se guardan (con frecuencia semanal, ~3 meses)
PAGINA = 1000


def cliente() -> tuple[str, dict]:
    load_dotenv(AQUI / ".env")
    url, key = os.getenv("SUPABASE_URL", "").rstrip("/"), os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        sys.exit("Falta SUPABASE_URL o SUPABASE_KEY en .env")
    if key.startswith("sb_publishable_"):
        sys.exit("SUPABASE_KEY es la clave pública: el respaldo necesita la sb_secret_.")
    return url, {"apikey": key, "Authorization": f"Bearer {key}"}


def descargar(url: str, h: dict, tabla: str) -> list[dict]:
    filas, desde = [], 0
    while True:
        r = requests.get(
            f"{url}/rest/v1/{tabla}?select=*&order={TABLAS[tabla]}",
            headers={**h, "Range-Unit": "items", "Range": f"{desde}-{desde + PAGINA - 1}"},
            timeout=60,
        )
        if r.status_code not in (200, 206):
            raise RuntimeError(f"{tabla}: HTTP {r.status_code} {r.text[:200]}")
        lote = r.json()
        filas.extend(lote)
        if len(lote) < PAGINA:
            return filas
        desde += PAGINA


def ultimo_respaldo() -> Path | None:
    archivos = sorted(CARPETA.glob("respaldo_*.json.gz"))
    return archivos[-1] if archivos else None


def respaldar(si_pasaron_dias: float | None) -> int:
    if si_pasaron_dias is not None:
        ult = ultimo_respaldo()
        if ult:
            dias = (time.time() - ult.stat().st_mtime) / 86400
            if dias < si_pasaron_dias:
                print(f"Respaldo: el último ({ult.name}) tiene {dias:.1f} días; no hace falta otro.")
                return 0

    url, h = cliente()
    CARPETA.mkdir(exist_ok=True)
    datos = {"creado": datetime.now().isoformat(timespec="seconds"), "tablas": {}}
    for t in TABLAS:
        datos["tablas"][t] = descargar(url, h, t)
        print(f"  {t}: {len(datos['tablas'][t])} filas")

    destino = CARPETA / f"respaldo_{datetime.now():%Y%m%d_%H%M}.json.gz"
    with gzip.open(destino, "wt", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, default=str)
    print(f"Respaldo guardado: {destino} ({destino.stat().st_size / 1024:.0f} KB)")

    for viejo in sorted(CARPETA.glob("respaldo_*.json.gz"))[:-CONSERVAR]:
        viejo.unlink()
        print(f"  (borrado respaldo viejo {viejo.name})")
    return 0


def restaurar(archivo: Path, tabla: str, dry_run: bool) -> int:
    if tabla not in RESTAURABLES:
        sys.exit(f"Solo se restauran: {', '.join(RESTAURABLES)}. "
                 "`productos` se regenera con la sincronización del ERP.")
    with gzip.open(archivo, "rt", encoding="utf-8") as f:
        datos = json.load(f)
    filas = datos["tablas"].get(tabla, [])
    print(f"{archivo.name} (creado {datos.get('creado')}): {len(filas)} filas de {tabla}")
    if dry_run or not filas:
        print("[DRY-RUN] No se escribió nada." if dry_run else "Nada para restaurar.")
        return 0

    url, h = cliente()
    clave = RESTAURABLES[tabla]
    for i in range(0, len(filas), 500):
        r = requests.post(
            f"{url}/rest/v1/{tabla}?on_conflict={clave}",
            headers={**h, "Content-Type": "application/json",
                     "Prefer": "resolution=merge-duplicates,return=minimal"},
            data=json.dumps(filas[i:i + 500], default=str),
            timeout=60,
        )
        if r.status_code not in (200, 201, 204):
            print(f"ERROR {r.status_code}: {r.text[:300]}")
            return 1
    print(f"Restauradas {len(filas)} filas en {tabla} (las que no estaban en el respaldo quedan como están).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Respaldo y restauración de datos de Supabase.")
    ap.add_argument("--si-pasaron-dias", type=float, default=None)
    ap.add_argument("--restaurar", type=Path)
    ap.add_argument("--tabla")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.restaurar:
        if not a.tabla:
            sys.exit("Indicá --tabla (catalogo_web o config_web).")
        return restaurar(a.restaurar, a.tabla, a.dry_run)
    return respaldar(a.si_pasaron_dias)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (requests.RequestException, RuntimeError) as e:
        print(f"ERROR en el respaldo: {e}")
        sys.exit(1)
