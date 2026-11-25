// Lista para presupuestar (REQ-029, D-008): vive SOLO en el navegador del
// visitante (localStorage) y se envía por WhatsApp o email. No hay precios ni
// datos personales del lado servidor.

import { useSyncExternalStore } from "react";

export type ItemLista = { codigo: number; nombre: string; slug: string; cant: number };

const CLAVE = "beta.presupuesto.v1";
export const MAX_ITEMS = 100;
export const MAX_CANT = 9999;

let cache: ItemLista[] = [];
let cargado = false;
const oyentes = new Set<() => void>();
const VACIA: ItemLista[] = [];

function leer(): ItemLista[] {
  try {
    const crudo = JSON.parse(localStorage.getItem(CLAVE) ?? "[]");
    if (!Array.isArray(crudo)) return [];
    return crudo
      .filter((x) => Number.isInteger(x?.codigo) && typeof x?.nombre === "string")
      .map((x) => ({ codigo: x.codigo, nombre: x.nombre, slug: String(x.slug ?? x.codigo), cant: acotar(x.cant) }))
      .slice(0, MAX_ITEMS);
  } catch {
    return []; // modo privado, almacenamiento bloqueado o dato corrupto
  }
}

function guardar(lista: ItemLista[]) {
  cache = lista;
  try {
    localStorage.setItem(CLAVE, JSON.stringify(lista));
  } catch {
    // sin almacenamiento: la lista funciona igual mientras la pestaña esté abierta
  }
  oyentes.forEach((f) => f());
}

function acotar(n: unknown): number {
  const v = Math.floor(Number(n));
  return Number.isFinite(v) ? Math.min(MAX_CANT, Math.max(1, v)) : 1;
}

function suscribir(f: () => void) {
  oyentes.add(f);
  const otraPestana = (e: StorageEvent) => {
    if (e.key === CLAVE) {
      cache = leer();
      f();
    }
  };
  window.addEventListener("storage", otraPestana);
  return () => {
    oyentes.delete(f);
    window.removeEventListener("storage", otraPestana);
  };
}

function instantanea(): ItemLista[] {
  if (!cargado) {
    cache = leer();
    cargado = true;
  }
  return cache;
}

export function useLista(): ItemLista[] {
  return useSyncExternalStore(suscribir, instantanea, () => VACIA);
}

export function agregar(p: { codigo: number; nombre: string; slug: string }, cant = 1) {
  const lista = instantanea();
  const i = lista.findIndex((x) => x.codigo === p.codigo);
  if (i >= 0) {
    guardar(lista.map((x, j) => (j === i ? { ...x, cant: acotar(x.cant + cant) } : x)));
  } else if (lista.length < MAX_ITEMS) {
    guardar([...lista, { ...p, cant: acotar(cant) }]);
  }
}

export function cambiarCantidad(codigo: number, cant: number) {
  guardar(instantanea().map((x) => (x.codigo === codigo ? { ...x, cant: acotar(cant) } : x)));
}

export function quitar(codigo: number) {
  guardar(instantanea().filter((x) => x.codigo !== codigo));
}

export function vaciar() {
  guardar([]);
}

// Formato pensado para cargarlo directo como presupuesto en el ERP.
export function mensajeLista(lista: ItemLista[], datos: { nombre?: string; localidad?: string; notas?: string }): string {
  const lineas = [
    "Pedido de cotización - Beta Electricidad",
    "",
    ...lista.map((x) => `${x.cant} x [${x.codigo}] ${x.nombre}`),
    "",
    `${lista.length} ${lista.length === 1 ? "producto" : "productos"}.`,
  ];
  if (datos.nombre?.trim()) lineas.push(`Nombre: ${datos.nombre.trim()}`);
  if (datos.localidad?.trim()) lineas.push(`Localidad: ${datos.localidad.trim()}`);
  if (datos.notas?.trim()) lineas.push(`Notas: ${datos.notas.trim()}`);
  return lineas.join("\n");
}
