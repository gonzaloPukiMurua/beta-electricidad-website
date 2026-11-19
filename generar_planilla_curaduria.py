"""
generar_planilla_curaduria.py — Planilla para elegir qué productos se publican en la web.

Genera curaduria/catalogo_web_seleccion.xlsx con todos los productos activos.
Los rubros del alcance de la fase 1 van primero y con la categoría sugerida.
Se marca "S" en "Publicar" y, opcionalmente, nombre web, URL de imagen y destacado.
Después se sube con:  python cargar_seleccion_catalogo.py

Si la planilla ya existe, la vuelve a generar CONSERVANDO lo que se cargó a mano
(Publicar, categoría, subcategoría, nombre web, URL, destacado, notas) y suma
los productos nuevos del ERP. La versión anterior queda como .bak.xlsx.

Uso:
    python generar_planilla_curaduria.py

Requiere .env con SUPABASE_URL y SUPABASE_KEY (sb_secret_). La planilla tiene
stock y queda en curaduria/, fuera del repo.
"""
import os
import shutil
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from planilla_xlsx import leer_hoja


AQUI = Path(__file__).parent
SALIDA = AQUI / "curaduria" / "catalogo_web_seleccion.xlsx"

# Rubro del ERP -> (categoría web, subcategoría web). Alcance de la fase 1.
MAPEO = {
    # Iluminación
    "APLIQUES": ("Iluminación", "Apliques"),
    "APLIQUE LED": ("Iluminación", "Apliques"),
    "COLGANTES METALICOS": ("Iluminación", "Colgantes"),
    "COLGANTES PLASTICOS": ("Iluminación", "Colgantes"),
    "COLGANTE VIDRIO": ("Iluminación", "Colgantes"),
    "COLGANTE LED": ("Iluminación", "Colgantes"),
    "COLGANTES FIBRA": ("Iluminación", "Colgantes"),
    "ARAÑAS": ("Iluminación", "Colgantes"),
    "SPOT GU10/AR111/E27": ("Iluminación", "Spots y embutidos"),
    "SPOT CABEZAL": ("Iluminación", "Spots y embutidos"),
    "SPOTS LINE": ("Iluminación", "Spots y embutidos"),
    "EMBUTIDO LED": ("Iluminación", "Spots y embutidos"),
    "EMBUTIDOS": ("Iluminación", "Spots y embutidos"),
    "FAROLES": ("Iluminación", "Faroles"),
    "FAROLAS/GLOBOS": ("Iluminación", "Faroles"),
    "PLAFON LED": ("Iluminación", "Plafones"),
    "PLAFON Y DIFUSOR": ("Iluminación", "Plafones"),
    "PROYECTORES LED": ("Iluminación", "Proyectores"),
    "PROYECTORES": ("Iluminación", "Proyectores"),
    "LAMPARA BULBO LED": ("Iluminación", "Lámparas"),
    "LAMPARA DICROICA LED": ("Iluminación", "Lámparas"),
    "LAMPARA FILAMENTO": ("Iluminación", "Lámparas"),
    "LAMPARA AR111 LED": ("Iluminación", "Lámparas"),
    "LAMPARA ALTA POTENCIA LED": ("Iluminación", "Lámparas"),
    "TUBO LED": ("Iluminación", "Lámparas"),
    "BIPIN LED": ("Iluminación", "Lámparas"),
    # Llaves y tomas
    "LLAVES": ("Llaves y tomas", "Llaves y tomas"),
    "LLAVES EXTERIOR": ("Llaves y tomas", "Exterior"),
    "TECLAS": ("Llaves y tomas", "Llaves y tomas"),
    "FICHAS DOMICILIARIAS": ("Llaves y tomas", "Fichas y adaptadores"),
    "ADAPTADOR Y TRIPLE": ("Llaves y tomas", "Fichas y adaptadores"),
    # Cables
    "CONDUCTORES": ("Cables", "Cables unipolares y conductores"),
    "SUBTERRANEO IRAM2178": ("Cables", "Subterráneos"),
    "CABLE PARALELO": ("Cables", "Paralelos y tipo taller"),
    "TIPO TALLER": ("Cables", "Paralelos y tipo taller"),
    "CABLE TV/TEL/UTP/ETC": ("Cables", "TV, telefonía y datos"),
    "PREENSAMBLADO": ("Cables", "Preensamblados"),
    # Cajas y tableros
    "CAJA BOCAS Y LLAVES": ("Cajas y tableros", "Cajas de embutir"),
    "CAJAS DE PASO IP40": ("Cajas y tableros", "Cajas de paso"),
    "CAJAS DE PASO IP65": ("Cajas y tableros", "Cajas de paso"),
    "TABLEROS IP40": ("Cajas y tableros", "Tableros"),
    "TABLERO IP65 Y PILAR": ("Cajas y tableros", "Tableros"),
    "GABINETE PLASTICO": ("Cajas y tableros", "Gabinetes"),
    "GABINETE METALICO": ("Cajas y tableros", "Gabinetes"),
    "CAJAS MEDIDORES": ("Cajas y tableros", "Cajas para medidor"),
    # Cañerías y accesorios
    "CAÑERIA PLASTICA": ("Cañerías y accesorios", "Caños"),
    "CAÑERIA METALICA": ("Cañerías y accesorios", "Caños"),
    "CAÑERIA FLEXIBLE": ("Cañerías y accesorios", "Caños"),
    "ACCESORIO CAÑERIA": ("Cañerías y accesorios", "Accesorios de cañería"),
    "FIJACION CAÑERIA": ("Cañerías y accesorios", "Fijación"),
    "PRENSA CAÑO/CABLE": ("Cañerías y accesorios", "Accesorios de cañería"),
    "CABLE CANAL": ("Cañerías y accesorios", "Cablecanal"),
    # Protecciones domiciliarias
    "TERMOMAGNETICAS": ("Protecciones", "Termomagnéticas"),
    "DIFERENCIALES": ("Protecciones", "Disyuntores diferenciales"),
    "PROTECTOR TENSION": ("Protecciones", "Protectores de tensión"),
    "DESCARGADOR ATMOS": ("Protecciones", "Descargadores"),
    # Agregados al ver la primera selección (2026-11-19)
    "LLAVES ARMADAS": ("Llaves y tomas", "Llaves armadas"),
    "LLAVE CAPSULADA": ("Llaves y tomas", "Llaves armadas"),
    "PORTALAMPARAS": ("Iluminación", "Portalámparas y accesorios"),
    "CABLES P/COLGANTES": ("Iluminación", "Portalámparas y accesorios"),
    "ARTEFACTOS P/TUBOS": ("Iluminación", "Artefactos para tubos"),
    "TUBOS FLUORESCENTES": ("Iluminación", "Lámparas"),
    "LAMPARA FANTASIA": ("Iluminación", "Lámparas"),
    "LAMPARA HALOGENA": ("Iluminación", "Lámparas"),
    "LAMPARAS PL": ("Iluminación", "Lámparas"),
    "LAMPARA BAJO CONSUMO": ("Iluminación", "Lámparas"),
    "TORTUGAS": ("Iluminación", "Tortugas"),
    "TORTUGA LED": ("Iluminación", "Tortugas"),
    "CINTA LED": ("Iluminación", "Cintas LED y fuentes"),
    "FUENTE CORRIENTE DC": ("Iluminación", "Cintas LED y fuentes"),
    "DRIVER LED": ("Iluminación", "Cintas LED y fuentes"),
    "LUZ EMERGENCIA": ("Iluminación", "Emergencia"),
    "EMERGENCIA": ("Iluminación", "Emergencia"),
    "FOTOCONTROL": ("Iluminación", "Fotocontroles y sensores"),
    "SENSOR MOVIMIENTO": ("Iluminación", "Fotocontroles y sensores"),
    "PILAR HORMIGON": ("Cajas y tableros", "Pilares y medidores"),
    "KIT PILAR": ("Cajas y tableros", "Pilares y medidores"),
    "ACCESORIOS PILAR": ("Cajas y tableros", "Pilares y medidores"),
    "MEDIDOR INTERNO": ("Cajas y tableros", "Pilares y medidores"),
    "PASACABLE": ("Cajas y tableros", "Accesorios para cajas y tableros"),
    "CINTA AISLADORA": ("Otros", "Cintas aisladoras"),
    "HERRAMIENTAS": ("Otros", "Herramientas"),
}
# Nombres de categoría de la selección inicial que cambiaron.
CATEGORIA_LEGADA = {"Llaves": "Llaves y tomas"}
CATEGORIAS = ["Iluminación", "Llaves y tomas", "Cables", "Cajas y tableros",
              "Cañerías y accesorios", "Protecciones", "Otros"]

COLUMNAS = [  # (título, ancho, editable)
    ("Código", 9, False), ("Cód. fábrica", 16, False), ("Descripción ERP", 46, False),
    ("Rubro ERP", 22, False), ("Marca", 14, False), ("Stock", 8, False),
    ("Publicar (S/N)", 9, True), ("Categoría", 20, True), ("Subcategoría", 24, True),
    ("Nombre web (opcional)", 34, True), ("URL imagen", 40, True),
    ("Destacado (S)", 9, True), ("Notas", 24, True),
]
EDITABLES = [c[0] for c in COLUMNAS if c[2]]


def leer_productos() -> list[dict]:
    load_dotenv(AQUI / ".env")
    url, key = os.getenv("SUPABASE_URL", "").rstrip("/"), os.getenv("SUPABASE_KEY", "")
    if not key or key.startswith("sb_publishable_"):
        sys.exit("SUPABASE_KEY en .env debe ser la sb_secret_.")
    h = {"apikey": key, "Authorization": f"Bearer {key}"}
    filas, desde = [], 0
    while True:
        r = requests.get(
            f"{url}/rest/v1/productos?select=codigo,codigo_alt,nombre,rubro,marca,stock"
            "&activo=eq.true&order=codigo",
            headers={**h, "Range": f"{desde}-{desde + 999}"}, timeout=60)
        r.raise_for_status()
        lote = r.json()
        filas += lote
        if len(lote) < 1000:
            break
        desde += 1000
    # lo ya publicado en la web (para no perderlo en la primera generación)
    r = requests.get(f"{url}/rest/v1/catalogo_web?select=*", headers=h, timeout=60)
    r.raise_for_status()
    web = {c["codigo"]: c for c in r.json()}
    return filas, web


def leer_anterior(ruta: Path) -> dict[int, dict]:
    if not ruta.exists():
        return {}
    rows = iter(leer_hoja(ruta, "Productos"))
    cab = [str(c) if c else "" for c in next(rows)]
    previo = {}
    for r in rows:
        d = dict(zip(cab, r))
        if d.get("Código") is None:
            continue
        datos = {k: d.get(k) for k in EDITABLES if d.get(k) not in (None, "")}
        if datos:
            previo[int(d["Código"])] = datos
    return previo


def main() -> int:
    productos, web = leer_productos()
    previo = leer_anterior(SALIDA)
    if SALIDA.exists():
        shutil.copy2(SALIDA, SALIDA.with_suffix(".bak.xlsx"))

    orden_rubro = {r: i for i, r in enumerate(MAPEO)}
    def clave(p):
        r = p["rubro"] or ""
        return (0, orden_rubro[r], p["nombre"] or "") if r in MAPEO else (1, r, p["nombre"] or "")
    productos.sort(key=clave)

    wb = Workbook()
    ws = wb.active
    ws.title = "Productos"
    ws.append([c[0] for c in COLUMNAS])
    gris = PatternFill("solid", fgColor="EEEEEE")
    amarillo = PatternFill("solid", fgColor="FFF6D5")
    for i, (titulo, ancho, editable) in enumerate(COLUMNAS, start=1):
        celda = ws.cell(row=1, column=i)
        celda.font = Font(bold=True)
        celda.fill = amarillo if editable else gris
        celda.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[celda.column_letter].width = ancho

    for p in productos:
        cat, sub = MAPEO.get(p["rubro"] or "", (None, None))
        w = web.get(p["codigo"], {})
        fila = {
            "Publicar (S/N)": "S" if w.get("publicado") else None,
            "Categoría": CATEGORIA_LEGADA.get(w.get("categoria_web"), w.get("categoria_web")) or cat,
            "Subcategoría": w.get("subcategoria_web") or sub,
            "Nombre web (opcional)": w.get("nombre_web"),
            "URL imagen": w.get("imagen_url"),
            "Destacado (S)": "S" if w.get("destacado") else None,
        }
        fila.update(previo.get(p["codigo"], {}))   # lo cargado a mano manda
        ws.append([
            p["codigo"], (p["codigo_alt"] or "").strip() or None, p["nombre"], p["rubro"], p["marca"],
            p["stock"], fila["Publicar (S/N)"], fila["Categoría"], fila["Subcategoría"],
            fila["Nombre web (opcional)"], fila["URL imagen"], fila["Destacado (S)"], fila.get("Notas"),
        ])

    n = ws.max_row
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:{ws.cell(row=1, column=len(COLUMNAS)).column_letter}{n}"
    sn = DataValidation(type="list", formula1='"S,N"', allow_blank=True)
    s_ = DataValidation(type="list", formula1='"S"', allow_blank=True)
    cats = DataValidation(type="list", formula1=f'"{",".join(CATEGORIAS)}"', allow_blank=True)
    for dv, col in ((sn, "G"), (cats, "H"), (s_, "L")):
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{n}")

    guia = wb.create_sheet("Instrucciones")
    for linea in [
        "Cómo usar esta planilla",
        "",
        "1. Filtrá por 'Rubro ERP' o 'Categoría' y marcá S en 'Publicar' los productos que van a la web. N o vacío = no se publica.",
        "2. Los rubros del alcance de la fase 1 ya tienen Categoría y Subcategoría sugeridas. Se pueden cambiar.",
        "3. 'Nombre web' es opcional: si queda vacío se usa la descripción del ERP.",
        "4. 'URL imagen': dirección directa de la foto (que empiece con https:// y termine en .jpg, .png o .webp). En el sitio del fabricante: clic derecho sobre la foto → 'Copiar dirección de imagen'.",
        "5. 'Destacado' = aparece primero en su categoría y en la portada.",
        "6. Las columnas grises vienen del ERP y no se editan acá.",
        "7. Para subir los cambios: python cargar_seleccion_catalogo.py --dry-run (revisar) y luego sin --dry-run.",
        "8. Para sumar productos nuevos del ERP: python generar_planilla_curaduria.py (conserva lo que ya cargaste).",
        "",
        "Categorías válidas: " + ", ".join(CATEGORIAS),
    ]:
        guia.append([linea])
    guia.column_dimensions["A"].width = 140
    guia["A1"].font = Font(bold=True, size=14)

    SALIDA.parent.mkdir(exist_ok=True)
    wb.save(SALIDA)
    sugeridos = sum(1 for p in productos if (p["rubro"] or "") in MAPEO)
    print(f"Planilla: {SALIDA}")
    print(f"  {len(productos)} productos activos; {sugeridos} en rubros sugeridos (arriba).")
    print(f"  Ya publicados: {sum(1 for c in web.values() if c.get('publicado'))}. "
          f"Datos conservados de la versión anterior: {len(previo)} filas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
