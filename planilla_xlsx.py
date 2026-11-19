"""
planilla_xlsx.py — Lector mínimo de valores de un .xlsx (solo lectura).

openpyxl falla con planillas guardadas por WPS, LibreOffice u otras apps
(estilos, validaciones o extensiones que no reconoce). Para la curaduría solo
hacen falta los valores, así que se leen directo del XML del archivo.
"""
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _col(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1


def _texto(nodo) -> str:
    return "".join(t.text or "" for t in nodo.iter(f"{{{NS['m']}}}t"))


def hojas(ruta: Path) -> list[str]:
    with zipfile.ZipFile(ruta) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        return [s.get("name") for s in wb.find("m:sheets", NS)]


def leer_hoja(ruta: Path, nombre: str) -> list[list]:
    """Devuelve las filas de la hoja como listas de valores (str, float o None)."""
    with zipfile.ZipFile(ruta) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rid = None
        for s in wb.find("m:sheets", NS):
            if s.get("name") == nombre:
                rid = s.get(f"{{{NS['r']}}}id")
        if rid is None:
            raise KeyError(f"La planilla no tiene la hoja '{nombre}'")
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        destino = next(r.get("Target") for r in rels.iter(f"{REL_NS}Relationship") if r.get("Id") == rid)
        destino = destino.lstrip("/")
        if not destino.startswith("xl/"):
            destino = "xl/" + destino

        compartidos = []
        if "xl/sharedStrings.xml" in z.namelist():
            sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
            compartidos = [_texto(si) for si in sst.findall("m:si", NS)]

        filas = []
        for fila in ET.fromstring(z.read(destino)).iter(f"{{{NS['m']}}}row"):
            valores = {}
            for i, c in enumerate(fila.findall("m:c", NS)):
                ref, tipo = c.get("r"), c.get("t")
                col = _col(ref) if ref else i
                v = c.find("m:v", NS)
                if tipo == "s" and v is not None:
                    valor = compartidos[int(v.text)]
                elif tipo == "inlineStr":
                    valor = _texto(c)
                elif tipo in ("str", "e") and v is not None:
                    valor = v.text
                elif tipo == "b" and v is not None:
                    valor = v.text == "1"
                elif v is not None and v.text is not None:
                    valor = float(v.text)
                    if valor.is_integer():
                        valor = int(valor)
                else:
                    valor = None
                valores[col] = valor
            if valores:
                filas.append([valores.get(j) for j in range(max(valores) + 1)])
        return filas
