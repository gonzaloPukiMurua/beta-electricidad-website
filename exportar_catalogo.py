"""
exportar_catalogo.py
--------------------
Exporta productos, stock y listas de precios desde el ERP Visual FoxPro
hacia un archivo Excel (.xlsx) listo para usar.

USO:
    python exportar_catalogo.py --datos "C:\a\datos"
    python exportar_catalogo.py --datos "C:\a\datos" --salida mi_catalogo.xlsx
    python exportar_catalogo.py --datos "C:\a\datos" --solo-con-stock
    python exportar_catalogo.py --datos "C:\a\datos" --solo-publicados

FILTROS (se pueden combinar):
    --solo-con-stock      Solo artículos con stock > 0
    --solo-publicados     Solo artículos con ARPUB = True (marcados para la web)

REQUISITOS:
    python -m pip install dbfread openpyxl

IMPORTANTE: Solo lectura — no modifica ningún archivo del ERP.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

try:
    from dbfread import DBF
except ImportError:
    sys.exit("Falta dbfread.  Instalalo con:  python -m pip install dbfread")

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit("Falta openpyxl.  Instalalo con:  python -m pip install openpyxl")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def abrir_dbf(ruta: Path, nombre: str):
    archivo = ruta / nombre
    if not archivo.exists():
        sys.exit(f"No se encontró el archivo: {archivo}")
    return DBF(str(archivo), encoding="latin-1", load=False,
               ignore_missing_memofile=True)


def cargar_lookup(ruta, nombre, campo_cod, campo_nom):
    resultado = {}
    try:
        for rec in abrir_dbf(ruta, nombre):
            cod = rec.get(campo_cod)
            nom = rec.get(campo_nom, "")
            if cod is not None:
                resultado[cod] = str(nom).strip()
    except Exception as e:
        print(f"  Advertencia: no se pudo cargar {nombre}: {e}")
    return resultado


def cargar_stock(ruta):
    stock = {}
    for rec in abrir_dbf(ruta, "STOCK.DBF"):
        art = rec.get("START")
        cant = rec.get("STCAN") or 0
        if art is not None:
            stock[art] = stock.get(art, 0) + cant
    return stock


def cargar_listas(ruta):
    listas = []
    for rec in abrir_dbf(ruta, "LISTAS.DBF"):
        listas.append({
            "nombre":  str(rec.get("LINOM", "")).strip(),
            "recargo": float(rec.get("LIREC") or 0),
        })
    return listas


# ---------------------------------------------------------------------------
# Extracción principal
# ---------------------------------------------------------------------------

def extraer_articulos(ruta: Path, solo_con_stock: bool, solo_publicados: bool) -> list[dict]:
    print("  Cargando catálogos auxiliares...")
    rubros = cargar_lookup(ruta, "RUBROS.DBF", "RUCOD", "RUNOM")
    marcas = cargar_lookup(ruta, "MARCAS.DBF", "MACOD", "MANOM")
    stock  = cargar_stock(ruta)
    listas = cargar_listas(ruta)

    print("  Leyendo artículos...")
    articulos = []
    omit_inactivos  = 0
    omit_sin_stock  = 0
    omit_no_pub     = 0

    for rec in abrir_dbf(ruta, "ARTICULO.DBF"):

        # Solo activos
        if str(rec.get("ARACT", "")).strip() != "S":
            omit_inactivos += 1
            continue

        cod      = rec.get("ARCOD")
        cant_stk = stock.get(cod, 0)
        publicado = bool(rec.get("ARPUB"))   # True / False / None → bool
        en_oferta = bool(rec.get("AROFE"))   # True si está en oferta

        if solo_con_stock and cant_stk <= 0:
            omit_sin_stock += 1
            continue

        if solo_publicados and not publicado:
            omit_no_pub += 1
            continue

        precio_base = float(rec.get("ARPRV") or 0)
        costo       = float(rec.get("ARPRC") or 0)

        precios_lista = {
            f"Lista: {l['nombre']}": round(precio_base * (1 + l["recargo"] / 100), 2)
            for l in listas
        }

        articulos.append({
            "Código":        cod,
            "Cód. Alt.":     str(rec.get("ARCOF") or "").strip() or str(rec.get("ARCOA") or "").strip(),
            "Nombre":        str(rec.get("ARNOM") or "").strip(),
            "Rubro":         rubros.get(rec.get("ARRUB"), ""),
            "Marca":         marcas.get(rec.get("ARMAR"), ""),
            "Precio venta":  precio_base,
            "Costo":         costo,
            "Stock":         cant_stk,
            "Publicado web": "Sí" if publicado else "No",
            "En oferta":     "Sí" if en_oferta else "No",
            **precios_lista,
        })

    print(f"  → {len(articulos)} artículos exportados")
    if omit_inactivos: print(f"     ({omit_inactivos} inactivos omitidos)")
    if omit_sin_stock: print(f"     ({omit_sin_stock} sin stock omitidos)")
    if omit_no_pub:    print(f"     ({omit_no_pub} no publicados omitidos)")

    return articulos


# ---------------------------------------------------------------------------
# Escritura Excel
# ---------------------------------------------------------------------------

HEADER_COLOR  = "2B5F8E"
ALT_ROW_COLOR = "EEF3F8"
PRICE_COLOR   = "FFF8E1"
OFFER_COLOR   = "FFE0B2"   # naranja suave para artículos en oferta

def borde():
    lado = Side(style="thin", color="CCCCCC")
    return Border(left=lado, right=lado, top=lado, bottom=lado)


def escribir_excel(articulos: list[dict], salida: Path):
    if not articulos:
        sys.exit("No hay artículos para exportar.")

    wb = Workbook()
    ws = wb.active
    ws.title = "Catálogo"

    columnas = list(articulos[0].keys())

    header_fill  = PatternFill("solid", fgColor=HEADER_COLOR)
    header_font  = Font(bold=True, color="FFFFFF", name="Arial", size=10)
    center_align = Alignment(horizontal="center", vertical="center")

    for col_idx, col_name in enumerate(columnas, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = center_align
        cell.border    = borde()

    alt_fill   = PatternFill("solid", fgColor=ALT_ROW_COLOR)
    price_fill = PatternFill("solid", fgColor=PRICE_COLOR)
    offer_fill = PatternFill("solid", fgColor=OFFER_COLOR)
    base_font  = Font(name="Arial", size=10)

    precio_cols = {i+1 for i, c in enumerate(columnas)
                   if c in ("Precio venta", "Costo") or c.startswith("Lista:")}

    anchos = {
        "Código": 10, "Cód. Alt.": 14, "Nombre": 45, "Rubro": 25,
        "Marca": 22, "Precio venta": 16, "Costo": 14, "Stock": 10,
        "Publicado web": 14, "En oferta": 12,
    }

    for row_idx, art in enumerate(articulos, start=2):
        es_oferta = art.get("En oferta") == "Sí"
        row_fill  = offer_fill if es_oferta else (alt_fill if row_idx % 2 == 0 else None)

        for col_idx, col_name in enumerate(columnas, start=1):
            valor = art[col_name]
            cell  = ws.cell(row=row_idx, column=col_idx, value=valor)
            cell.font   = base_font
            cell.border = borde()
            if col_idx in precio_cols:
                cell.fill = price_fill
                if isinstance(valor, (int, float)):
                    cell.number_format = '#,##0.00'
            else:
                if row_fill:
                    cell.fill = row_fill

    for col_idx, col_name in enumerate(columnas, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = anchos.get(col_name, 18)

    ws.freeze_panes = "A2"

    # Hoja de stats
    ws_meta = wb.create_sheet("Info exportación")
    stats = [
        ("Generado el",           datetime.now().strftime("%d/%m/%Y %H:%M")),
        ("Total artículos",        len(articulos)),
        ("Con stock > 0",          sum(1 for a in articulos if (a.get("Stock") or 0) > 0)),
        ("Publicados en web",      sum(1 for a in articulos if a.get("Publicado web") == "Sí")),
        ("En oferta",              sum(1 for a in articulos if a.get("En oferta") == "Sí")),
        ("Script",                 "exportar_catalogo.py — solo lectura"),
    ]
    for i, (k, v) in enumerate(stats, start=1):
        ws_meta.cell(row=i, column=1, value=k).font = Font(bold=True, name="Arial")
        ws_meta.cell(row=i, column=2, value=v)
    ws_meta.column_dimensions["A"].width = 25
    ws_meta.column_dimensions["B"].width = 40

    wb.save(str(salida))
    print(f"\n✓ Archivo guardado en: {salida.resolve()}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Exporta el catálogo del ERP FoxPro a Excel (solo lectura)."
    )
    parser.add_argument("--datos",           default="datos",
                        help='Ruta a la carpeta datos del ERP (ej: "C:\\a\\datos")')
    parser.add_argument("--salida",          default=None,
                        help="Nombre del Excel de salida")
    parser.add_argument("--solo-con-stock",  action="store_true",
                        help="Solo artículos con stock > 0")
    parser.add_argument("--solo-publicados", action="store_true",
                        help="Solo artículos con ARPUB=True (marcados para la web en el ERP)")
    args = parser.parse_args()

    ruta_datos = Path(args.datos)
    if not ruta_datos.is_dir():
        sys.exit(f"No se encontró la carpeta: {ruta_datos.resolve()}")

    nombre_salida = args.salida or f"catalogo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    ruta_salida   = Path(nombre_salida)

    print(f"\nExportando catálogo desde: {ruta_datos.resolve()}")
    print(f"  --solo-con-stock:  {'Sí' if args.solo_con_stock  else 'No'}")
    print(f"  --solo-publicados: {'Sí' if args.solo_publicados else 'No'}\n")

    articulos = extraer_articulos(ruta_datos, args.solo_con_stock, args.solo_publicados)
    escribir_excel(articulos, ruta_salida)
    print("\nListo.")


if __name__ == "__main__":
    main()
