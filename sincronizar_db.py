"""
sincronizar_db.py
-----------------
Lee el archivo de cambios generado por detectar_cambios.py y sincroniza
la base de datos Supabase (upsert de nuevos/modificados, baja de eliminados).

FLUJO COMPLETO:
    1. python exportar_catalogo.py --datos "C:/a/datos"
           → catalogo_YYYYMMDD.xlsx   (snapshot completo, guardar como referencia)

    2. python detectar_cambios.py --datos "C:/a/datos" --anterior catalogo_anterior.xlsx
           → cambios_YYYYMMDD.xlsx

    3. python sincronizar_db.py --cambios cambios_YYYYMMDD.xlsx
           → sube solo lo que cambió a Supabase

USO:
    python sincronizar_db.py --cambios cambios_YYYYMMDD.xlsx
    python sincronizar_db.py --cambios cambios_YYYYMMDD.xlsx --dry-run   # simula sin tocar la DB
    python sincronizar_db.py --inicial catalogo_completo.xlsx            # carga inicial completa

CONFIGURACIÓN:
    Crear un archivo .env en la misma carpeta con:
        SUPABASE_URL=https://xxxx.supabase.co
        SUPABASE_KEY=tu_service_role_key_aqui

    O bien definir esas variables de entorno directamente en el sistema.

REQUISITOS:
    python -m pip install openpyxl python-dotenv requests

IMPORTANTE: No toca el ERP. Opera solo sobre el Excel de cambios y Supabase.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    from openpyxl import load_workbook
except ImportError:
    sys.exit("Falta openpyxl.  Instalalo con:  python -m pip install openpyxl")

try:
    import requests
except ImportError:
    sys.exit("Falta requests.  Instalalo con:  python -m pip install requests")

# dotenv es opcional pero recomendado
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass   # sin dotenv: las variables deben estar en el entorno del sistema


# ---------------------------------------------------------------------------
# Configuración Supabase
# ---------------------------------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Nombre de la tabla en Supabase (podés cambiarla)
TABLA = "productos"

# Mapeo Excel → columna en Supabase
# Clave: nombre de columna en el Excel
# Valor: nombre de columna en la tabla Supabase
MAPEO_COLUMNAS = {
    "Código":        "codigo",
    "Cód. Alt.":     "codigo_alt",
    "Nombre":        "nombre",
    "Rubro":         "rubro",
    "Marca":         "marca",
    "Precio venta":  "precio_venta",
    "Costo":         "costo",
    "Stock":         "stock",
    # "Publicado web" y "En oferta" NO se sincronizan: la curaduría vive en la
    # tabla `catalogo_web` y la decide el negocio desde el admin (REQ-013, D-004).
    # Antes se pisaban con el valor del ERP (ARPUB) en cada artículo modificado.
    # Las listas de precio se mapean dinámicamente más abajo
}

# Columnas de listas de precio → prefijo en Supabase
PREFIJO_LISTA = "lista_"   # "Lista: NORMAL" → "lista_normal"


# ---------------------------------------------------------------------------
# Cliente Supabase (sin SDK, solo REST)
# ---------------------------------------------------------------------------

class SupabaseClient:
    def __init__(self, url: str, key: str, dry_run: bool = False):
        self.url     = url.rstrip("/")
        self.headers = {
            "apikey":        key,
            "Authorization": f"Bearer {key}",
            "Content-Type":  "application/json",
            "Prefer":        "return=minimal",
        }
        self.dry_run = dry_run

    def _endpoint(self, tabla: str) -> str:
        return f"{self.url}/rest/v1/{tabla}"

    def upsert(self, tabla: str, rows: list[dict]) -> dict:
        """Inserta o actualiza filas. Usa 'codigo' como clave de conflicto."""
        if self.dry_run:
            print(f"    [DRY-RUN] upsert {len(rows)} filas en '{tabla}'")
            return {"ok": True, "count": len(rows)}

        headers = {**self.headers, "Prefer": "resolution=merge-duplicates,return=minimal"}
        # on_conflict=codigo: sin esto PostgREST resuelve por la PK (`id`), que
        # no viene del ERP, e intenta insertar como nuevos los que ya existen.
        resp = requests.post(
            f"{self._endpoint(tabla)}?on_conflict=codigo",
            headers=headers,
            data=json.dumps(rows),
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            return {"ok": False, "status": resp.status_code, "error": resp.text}
        return {"ok": True, "count": len(rows)}

    def deactivate(self, tabla: str, codigos: list) -> dict:
        """Marca artículos eliminados como inactivos (no los borra físicamente)."""
        if self.dry_run:
            print(f"    [DRY-RUN] desactivar {len(codigos)} artículos en '{tabla}'")
            return {"ok": True, "count": len(codigos)}

        # PATCH con filtro por codigo
        params  = f"codigo=in.({','.join(str(c) for c in codigos)})"
        resp = requests.patch(
            f"{self._endpoint(tabla)}?{params}",
            headers=self.headers,
            data=json.dumps({"activo": False, "stock": 0}),
            timeout=30,
        )
        if resp.status_code not in (200, 204):
            return {"ok": False, "status": resp.status_code, "error": resp.text}
        return {"ok": True, "count": len(codigos)}

    def ping(self) -> bool:
        """Verifica que la conexión y la tabla existen."""
        try:
            resp = requests.get(
                f"{self._endpoint(TABLA)}?limit=1",
                headers=self.headers,
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Lectura del Excel
# ---------------------------------------------------------------------------

def limpiar_nombre_lista(nombre_col: str) -> str:
    """'Lista: GREMIO/INSTALADOR' → 'lista_gremio_instalador'"""
    import re
    nombre = nombre_col.replace("Lista: ", "").lower()
    nombre = re.sub(r'[^a-z0-9]+', '_', nombre)   # cualquier char no alfanumérico → _
    nombre = nombre.strip('_')                       # sacar _ al inicio/fin
    return PREFIJO_LISTA + nombre


def fila_a_registro(fila: dict, columnas: list[str]) -> dict:
    """Convierte una fila del Excel al formato de la tabla Supabase."""
    registro = {"activo": True}
    for col in columnas:
        valor = fila.get(col)
        # Normalizar
        if isinstance(valor, float) and valor != valor:   # NaN
            valor = None
        if col in MAPEO_COLUMNAS:
            registro[MAPEO_COLUMNAS[col]] = valor
        elif col.startswith("Lista:"):
            registro[limpiar_nombre_lista(col)] = valor
        # Ignorar columna "Cambios" si existe
    return registro


def leer_hoja(ws) -> tuple[list[str], list[dict]]:
    filas = list(ws.iter_rows(values_only=True))
    if not filas:
        return [], []
    columnas = [str(c) if c is not None else "" for c in filas[0]]
    registros = [dict(zip(columnas, f)) for f in filas[1:] if any(v is not None for v in f)]
    return columnas, registros


def leer_cambios(ruta: Path):
    """Lee el Excel de cambios y devuelve (upserts, codigos_a_desactivar)."""
    wb = load_workbook(str(ruta), read_only=True, data_only=True)
    hojas = wb.sheetnames

    upserts    = []
    desactivar = []

    for hoja in ["Modificados", "Nuevos", "Catálogo"]:
        if hoja in hojas:
            cols, filas = leer_hoja(wb[hoja])
            for f in filas:
                upserts.append(fila_a_registro(f, cols))

    if "Eliminados" in hojas:
        _, filas = leer_hoja(wb["Eliminados"])
        desactivar = [f.get("Código") for f in filas if f.get("Código")]

    wb.close()

    # `nombre` es obligatorio en la tabla: un artículo sin descripción en el ERP
    # haría fallar todo su lote. Se saltea y se avisa para corregirlo en el ERP.
    sin_nombre = [r.get("codigo") for r in upserts if not str(r.get("nombre") or "").strip()]
    if sin_nombre:
        print(f"  AVISO: {len(sin_nombre)} artículo(s) sin descripción en el ERP, no se suben: "
              f"{', '.join(str(c) for c in sin_nombre)}")
        upserts = [r for r in upserts if str(r.get("nombre") or "").strip()]

    return upserts, desactivar


# ---------------------------------------------------------------------------
# Sincronización con reintentos
# ---------------------------------------------------------------------------

BATCH_SIZE = 200   # filas por llamada a la API


def sincronizar(client: SupabaseClient, upserts: list[dict], desactivar: list, dry_run: bool):
    total_ok  = 0
    total_err = 0

    # --- Upserts en batches ---
    if upserts:
        print(f"\n  Subiendo {len(upserts)} artículos en batches de {BATCH_SIZE}...")
        for i in range(0, len(upserts), BATCH_SIZE):
            batch = upserts[i:i + BATCH_SIZE]
            n     = i // BATCH_SIZE + 1
            total = (len(upserts) + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"    Batch {n}/{total} ({len(batch)} filas)...", end=" ", flush=True)

            for intento in range(3):
                res = client.upsert(TABLA, batch)
                if res["ok"]:
                    total_ok += len(batch)
                    print("✓")
                    break
                else:
                    if intento < 2:
                        print(f"reintentando ({res.get('status')})...", end=" ", flush=True)
                        time.sleep(2)
                    else:
                        total_err += len(batch)
                        print(f"✗ ERROR: {res.get('error', '')[:80]}")

    # --- Desactivar eliminados ---
    if desactivar:
        print(f"\n  Desactivando {len(desactivar)} artículos eliminados...", end=" ", flush=True)
        res = client.deactivate(TABLA, desactivar)
        if res["ok"]:
            print("✓")
        else:
            print(f"✗ ERROR: {res.get('error', '')[:80]}")
            total_err += len(desactivar)

    return total_ok, total_err


# ---------------------------------------------------------------------------
# SQL para crear la tabla en Supabase (se imprime como referencia)
# ---------------------------------------------------------------------------

DDL_TABLA = """

-- Referencia histórica de la tabla `productos`. El esquema vigente (RLS,
-- catalogo_web, vista catalogo_publico) está en supabase/migrations/.
-- Ejecutar UNA SOLA VEZ en el SQL Editor de Supabase:

CREATE TABLE IF NOT EXISTS productos (
    id              BIGSERIAL PRIMARY KEY,
    codigo          INTEGER UNIQUE NOT NULL,
    codigo_alt      TEXT,
    nombre          TEXT NOT NULL,
    rubro           TEXT,
    marca           TEXT,
    precio_venta    NUMERIC(12, 2),
    costo           NUMERIC(12, 2),
    stock           NUMERIC(10, 2),
    publicado_web   BOOLEAN DEFAULT FALSE,
    en_oferta       BOOLEAN DEFAULT FALSE,
    activo          BOOLEAN DEFAULT TRUE,
    -- Listas de precio (generadas automáticamente desde el ERP)
    lista_normal                         NUMERIC(12, 2),
    lista_dto_especial                   NUMERIC(12, 2),
    lista_tarjeta_6_cuotas               NUMERIC(12, 2),
    lista_debito                         NUMERIC(12, 2),
    lista_gremio_instalador              NUMERIC(12, 2),
    lista_dto_gremio_espec               NUMERIC(12, 2),
    lista_tarjeta_3_cuotas               NUMERIC(12, 2),
    lista_tarjeta_2_cuotas               NUMERIC(12, 2),
    lista_getnet_1_cuota                 NUMERIC(12, 2),
    lista_simple_3_cuotas                NUMERIC(12, 2),
    lista_simple_6_cuotas                NUMERIC(12, 2),
    lista_plan_z                         NUMERIC(12, 2),
    lista_naranja_cobro                  NUMERIC(12, 2),
    lista_mercadopago_1_cuota            NUMERIC(12, 2),
    lista_mercadopago_3_cuotas           NUMERIC(12, 2),
    lista_mercadopago_6_cuotas           NUMERIC(12, 2),
    lista_mercadopago_2_cuotas           NUMERIC(12, 2),
    -- Timestamps automáticos
    creado_en       TIMESTAMPTZ DEFAULT NOW(),
    actualizado_en  TIMESTAMPTZ DEFAULT NOW()
);

-- Índices útiles para el e-commerce
CREATE INDEX IF NOT EXISTS idx_productos_publicado  ON productos (publicado_web) WHERE activo = TRUE;
CREATE INDEX IF NOT EXISTS idx_productos_oferta     ON productos (en_oferta)     WHERE activo = TRUE;
CREATE INDEX IF NOT EXISTS idx_productos_rubro      ON productos (rubro);
CREATE INDEX IF NOT EXISTS idx_productos_nombre     ON productos USING gin(to_tsvector('spanish', nombre));

-- Trigger para actualizar automáticamente 'actualizado_en'
CREATE OR REPLACE FUNCTION set_actualizado_en()
RETURNS TRIGGER AS $$ BEGIN NEW.actualizado_en = NOW(); RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_productos_actualizado
    BEFORE UPDATE ON productos
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();

"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza cambios del ERP con la base de datos Supabase."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--cambios",  help="Excel de cambios generado por detectar_cambios.py")
    group.add_argument("--inicial",  help="Excel completo para carga inicial (primer uso)")
    group.add_argument("--mostrar-sql", action="store_true",
                       help="Muestra el SQL para crear la tabla en Supabase y sale")

    parser.add_argument("--dry-run", action="store_true",
                        help="Simula la sincronización sin modificar la base de datos")
    args = parser.parse_args()

    # Solo mostrar SQL
    if args.mostrar_sql:
        print(DDL_TABLA)
        return

    # Validar credenciales
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n⚠️  No se encontraron las credenciales de Supabase.")
        print("   Creá un archivo .env en esta carpeta con el siguiente contenido:\n")
        print("   SUPABASE_URL=https://xxxx.supabase.co")
        print("   SUPABASE_KEY=tu_service_role_key_aqui\n")
        print("   Luego instalá python-dotenv:  python -m pip install python-dotenv")
        sys.exit(1)

    ruta_excel = Path(args.cambios or args.inicial)
    if not ruta_excel.exists():
        sys.exit(f"No se encontró el archivo: {ruta_excel}")

    client = SupabaseClient(SUPABASE_URL, SUPABASE_KEY, dry_run=args.dry_run)

    if args.dry_run:
        print("\n⚡ MODO DRY-RUN — no se modificará la base de datos\n")
    else:
        print(f"\nVerificando conexión con Supabase...")
        if not client.ping():
            print("✗ No se pudo conectar a Supabase.")
            print("  Verificá la URL, la key y que la tabla 'productos' exista.")
            print("  Para ver el SQL de creación: python sincronizar_db.py --mostrar-sql")
            sys.exit(1)
        print("✓ Conexión OK\n")

    print(f"Leyendo: {ruta_excel.name}")
    upserts, desactivar = leer_cambios(ruta_excel)
    print(f"  Artículos a subir/actualizar: {len(upserts)}")
    print(f"  Artículos a desactivar:       {len(desactivar)}")

    if not upserts and not desactivar:
        print("\nNada para sincronizar.")
        return

    inicio     = time.time()
    ok, errores = sincronizar(client, upserts, desactivar, args.dry_run)
    elapsed    = time.time() - inicio

    print(f"\n{'─'*40}")
    print(f"  Subidos correctamente: {ok}")
    if errores:
        print(f"  Con errores:           {errores}")
    print(f"  Tiempo:                {elapsed:.1f}s")
    print(f"{'─'*40}")
    print("\nSincronización completa." if not errores else "\nSincronización con errores — revisá los mensajes arriba.")
    if errores:
        sys.exit(1)   # para que sincronizar.bat (y la tarea programada) lo registre como falla


if __name__ == "__main__":
    main()