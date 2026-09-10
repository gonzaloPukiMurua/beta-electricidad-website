"""
detectar_cambios.py
-------------------
Compara el estado actual del ERP contra el último Excel exportado y genera
un archivo con SOLO los artículos que cambiaron.

USO:
    python detectar_cambios.py --datos "C:/a/datos" --anterior catalogo_anterior.xlsx
    python detectar_cambios.py --datos "C:/a/datos" --anterior catalogo_anterior.xlsx --solo-publicados

    Si no existe el archivo anterior, exporta todo como base inicial.

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
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit("Falta openpyxl.  Instalalo con:  python -m pip install openpyxl")

# Importamos las funciones de extracción del script principal
# (ambos scripts deben estar en la misma carpeta)
try:
    from exportar_catalogo import (
        abrir_dbf, cargar_lookup, cargar_stock, cargar_listas, escribir_excel
    )
except ImportError:
    sys.exit("exportar_catalogo.py debe estar en la misma carpeta que este script.")


# ---------------------------------------------------------------------------
# Extracción con todos los campos (incluyendo ARPUB y AROFE)
# ---------------------------------------------------------------------------

def extraer_actual(ruta: Path, solo_publicados: bool) -> dict:
    rubros = cargar_lookup(ruta, "RUBROS.DBF", "RUCOD", "RUNOM")
    marcas = cargar_lookup(ruta, "MARCAS.DBF", "MACOD", "MANOM")
    stock  = cargar_stock(ruta)
    listas = cargar_listas(ruta)

    articulos = {}
    omit_no_pub = 0

    for rec in abrir_dbf(ruta, "ARTICULO.DBF"):
        if str(rec.get("ARACT", "")).strip() != "S":
            continue

        cod       = rec.get("ARCOD")
        publicado = bool(rec.get("ARPUB"))
        en_oferta = bool(rec.get("AROFE"))

        if solo_publicados and not publicado:
            omit_no_pub += 1
            continue

        precio_base = float(rec.get("ARPRV") or 0)
        costo       = float(rec.get("ARPRC") or 0)

        precios_lista = {
            f"Lista: {l['nombre']}": round(precio_base * (1 + l["recargo"] / 100), 2)
            for l in listas
        }

        articulos[cod] = {
            "Código":        cod,
            "Cód. Alt.":     str(rec.get("ARCOF") or "").strip() or str(rec.get("ARCOA") or "").strip(),
            "Nombre":        str(rec.get("ARNOM") or "").strip(),
            "Rubro":         rubros.get(rec.get("ARRUB"), ""),
            "Marca":         marcas.get(rec.get("ARMAR"), ""),
            "Precio venta":  precio_base,
            "Costo":         costo,
            "Stock":         stock.get(cod, 0),
            "Publicado web": "Sí" if publicado else "No",
            "En oferta":     "Sí" if en_oferta else "No",
            **precios_lista,
        }

    if omit_no_pub:
        print(f"     ({omit_no_pub} no publicados omitidos)")
    return articulos


# ---------------------------------------------------------------------------
# Leer Excel anterior
# ---------------------------------------------------------------------------

def cargar_anterior(ruta_excel: Path) -> dict:
    print(f"  Leyendo archivo anterior: {ruta_excel.name} ...")
    wb = load_workbook(str(ruta_excel), read_only=True, data_only=True)
    hoja = "Catálogo" if "Catálogo" in wb.sheetnames else wb.sheetnames[0]
    ws   = wb[hoja]
    filas = list(ws.iter_rows(values_only=True))
    if not filas:
        return {}
    encabezados = [str(c) if c is not None else "" for c in filas[0]]
    anterior = {}
    for fila in filas[1:]:
        d   = dict(zip(encabezados, fila))
        cod = d.get("Código")
        if cod is not None:
            anterior[cod] = d
    wb.close()
    return anterior


# ---------------------------------------------------------------------------
# Comparación
# ---------------------------------------------------------------------------

CAMPOS_COMPARAR = ["Nombre", "Rubro", "Marca", "Precio venta", "Costo",
                   "Stock", "Publicado web", "En oferta"]


def normalizar(v):
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    if v in (None, ""):
        return None
    return str(v).strip()


def detectar_cambios(actual: dict, anterior: dict):
    modificados, nuevos, eliminados = [], [], []
    listas_cols = [k for k in next(iter(actual.values()), {}) if k.startswith("Lista:")]

    for cod, art in actual.items():
        if cod not in anterior:
            art["Cambios"] = "NUEVO"
            nuevos.append(art)
            continue
        prev  = anterior[cod]
        diffs = []
        for campo in CAMPOS_COMPARAR + listas_cols:
            if normalizar(art.get(campo)) != normalizar(prev.get(campo)):
                label = campo.replace("Lista: ", "") if campo.startswith("Lista:") else campo
                diffs.append(label)
        if diffs:
            art["Cambios"] = ", ".join(diffs)
            modificados.append(art)

    for cod, prev in anterior.items():
        if cod not in actual:
            eliminados.append({
                "Código":  cod,
                "Nombre":  prev.get("Nombre", ""),
                "Cambios": "ELIMINADO / INACTIVO",
            })

    return modificados, nuevos, eliminados


# ---------------------------------------------------------------------------
# Escritura Excel de cambios
# ---------------------------------------------------------------------------

COLORES = {
    "header":     "2B5F8E",
    "nuevo":      "C8E6C9",
    "modificado": "FFF9C4",
    "eliminado":  "FFCDD2",
}


def borde():
    lado = Side(style="thin", color="CCCCCC")
    return Border(left=lado, right=lado, top=lado, bottom=lado)


def escribir_hoja(ws, filas, color_fondo, columnas):
    hf = PatternFill("solid", fgColor=COLORES["header"])
    ff = Font(bold=True, color="FFFFFF", name="Arial", size=10)
    for ci, cn in enumerate(columnas, 1):
        c = ws.cell(1, ci, cn)
        c.font = ff; c.fill = hf
        c.alignment = Alignment(horizontal="center"); c.border = borde()

    fila_fill   = PatternFill("solid", fgColor=color_fondo)
    precio_cols = {i+1 for i, c in enumerate(columnas)
                   if c in ("Precio venta", "Costo") or c.startswith("Lista:")}

    for ri, art in enumerate(filas, 2):
        for ci, cn in enumerate(columnas, 1):
            v = art.get(cn, "")
            c = ws.cell(ri, ci, v)
            c.fill = fila_fill; c.font = Font(name="Arial", size=10); c.border = borde()
            if ci in precio_cols and isinstance(v, (int, float)):
                c.number_format = '#,##0.00'

    ws.freeze_panes = "A2"
    anchos = {"Código": 10, "Nombre": 45, "Rubro": 25, "Marca": 22,
              "Precio venta": 16, "Costo": 14, "Stock": 10,
              "Publicado web": 14, "En oferta": 12, "Cambios": 38}
    for ci, cn in enumerate(columnas, 1):
        ws.column_dimensions[get_column_letter(ci)].width = anchos.get(cn, 18)


def escribir_excel_cambios(modificados, nuevos, eliminados, columnas_base, salida):
    wb  = Workbook()
    total = len(modificados) + len(nuevos) + len(eliminados)

    if total == 0:
        ws = wb.active; ws.title = "Sin cambios"
        ws["A1"] = "No se detectaron cambios respecto al archivo anterior."
        wb.save(str(salida)); return

    ws_res = wb.active; ws_res.title = "Resumen"
    ws_res["A1"] = "Resumen de cambios"
    ws_res["A1"].font = Font(bold=True, size=13, name="Arial")
    for i, (k, v) in enumerate([
        ("Modificados", len(modificados)), ("Nuevos", len(nuevos)),
        ("Eliminados",  len(eliminados)),  ("TOTAL", total),
        ("Generado el", datetime.now().strftime("%d/%m/%Y %H:%M")),
    ], start=3):
        ws_res.cell(i, 1, k).font = Font(bold=(k == "TOTAL"), name="Arial")
        ws_res.cell(i, 2, v)

    cols_cambio = columnas_base + ["Cambios"]
    if modificados:
        escribir_hoja(wb.create_sheet("Modificados"), modificados, COLORES["modificado"], cols_cambio)
    if nuevos:
        escribir_hoja(wb.create_sheet("Nuevos"),      nuevos,      COLORES["nuevo"],      cols_cambio)
    if eliminados:
        escribir_hoja(wb.create_sheet("Eliminados"),  eliminados,  COLORES["eliminado"],
                      ["Código", "Nombre", "Cambios"])

    wb.save(str(salida))
    print(f"\n✓ Cambios guardados en: {salida.resolve()}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Detecta cambios entre el ERP y el último Excel exportado."
    )
    parser.add_argument("--datos",           default="datos")
    parser.add_argument("--anterior",        required=True,
                        help="Excel exportado anteriormente (para comparar)")
    parser.add_argument("--salida",          default=None)
    parser.add_argument("--solo-publicados", action="store_true",
                        help="Comparar solo artículos con ARPUB=True")
    args = parser.parse_args()

    ruta_datos  = Path(args.datos)
    ruta_ant    = Path(args.anterior)
    ruta_salida = Path(args.salida or f"cambios_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx")

    if not ruta_datos.is_dir():
        sys.exit(f"No se encontró la carpeta: {ruta_datos.resolve()}")

    print(f"\nLeyendo ERP desde: {ruta_datos.resolve()}")
    actual = extraer_actual(ruta_datos, args.solo_publicados)
    print(f"  → {len(actual)} artículos en el ERP")

    if not ruta_ant.exists():
        print(f"\nNo existe '{ruta_ant}' — exportando todo como base inicial.")
        escribir_excel(list(actual.values()), ruta_salida)
        return

    anterior = cargar_anterior(ruta_ant)
    print(f"  → {len(anterior)} artículos en el archivo anterior\n")

    modificados, nuevos, eliminados = detectar_cambios(actual, anterior)
    print(f"Comparando...")
    print(f"  Modificados: {len(modificados)}")
    print(f"  Nuevos:      {len(nuevos)}")
    print(f"  Eliminados:  {len(eliminados)}")

    if not (modificados or nuevos or eliminados):
        print("\n✓ Sin cambios detectados.")
        return

    columnas_base = [k for k in next(iter(actual.values())) if k != "Cambios"]
    escribir_excel_cambios(modificados, nuevos, eliminados, columnas_base, ruta_salida)
    print("\nListo.")


if __name__ == "__main__":
    main()
