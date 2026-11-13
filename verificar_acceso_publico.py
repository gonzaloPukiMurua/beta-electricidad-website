"""
verificar_acceso_publico.py — Prueba de aceptación de REQ-010 (solo lectura).

Usa la clave PÚBLICA del sitio (la misma que llega al navegador) y verifica:
  1. Que NO se pueda leer la tabla `productos` (costo, precio base, listas).
  2. Que la vista `catalogo_publico` se pueda leer.
  3. Que la vista NO tenga columnas sensibles.

Uso:
    python verificar_acceso_publico.py
Lee NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY de
beta-electricidad-full-app/.env.local. No escribe nada.
Sale con código 1 si alguna verificación falla.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENV = Path(__file__).parent / "beta-electricidad-full-app" / ".env.local"
PROHIBIDAS = {"costo", "precio_venta", "stock"}  # + cualquier lista_*


def cargar_env() -> tuple[str, str]:
    env = {}
    for linea in ENV.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*)\s*$", linea)
        if m:
            env[m[1]] = m[2].strip().strip('"')
    return env["NEXT_PUBLIC_SUPABASE_URL"].rstrip("/"), env["NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"]


def get(url: str, key: str, path: str):
    req = urllib.request.Request(url + path, headers={"apikey": key, "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]


def main() -> int:
    url, key = cargar_env()
    fallas = 0

    s, body = get(url, key, "/rest/v1/productos?select=codigo,costo&limit=5")
    if s == 200 and isinstance(body, list) and body:
        print(f"[FALLA] La clave pública lee `productos` ({len(body)} filas de muestra, con costo).")
        fallas += 1
    else:
        print(f"[OK]    `productos` cerrada para la clave pública (HTTP {s}).")

    s, body = get(url, key, "/rest/v1/catalogo_publico?select=*&limit=3")
    if s != 200:
        print(f"[FALLA] No se puede leer `catalogo_publico` (HTTP {s}): {body}")
        fallas += 1
    else:
        print(f"[OK]    `catalogo_publico` legible ({len(body)} filas de muestra).")
        if body:
            cols = set(body[0])
            malas = sorted(c for c in cols if c in PROHIBIDAS or c.startswith("lista_"))
            if malas:
                print(f"[FALLA] La vista expone columnas sensibles: {', '.join(malas)}")
                fallas += 1
            else:
                print(f"[OK]    Columnas de la vista: {', '.join(sorted(cols))}")
        else:
            print("        (La vista está vacía: todavía no hay productos publicados en `catalogo_web`.)")

    for tabla in ("catalogo_web", "config_web", "admins"):
        s, body = get(url, key, f"/rest/v1/{tabla}?select=*&limit=1")
        if s == 200 and isinstance(body, list) and body:
            print(f"[FALLA] La clave pública lee `{tabla}`.")
            fallas += 1
        else:
            print(f"[OK]    `{tabla}` cerrada para la clave pública (HTTP {s}).")

    print("\nResultado:", "TODO OK" if not fallas else f"{fallas} falla(s)")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
