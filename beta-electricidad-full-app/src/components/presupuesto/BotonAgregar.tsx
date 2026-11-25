"use client";

import { useState } from "react";
import Link from "next/link";
import { agregar, MAX_CANT, useLista, type ItemLista } from "@/lib/presupuesto";
import { textoBulto } from "@/lib/catalogo";

type P = Omit<ItemLista, "cant">;

// Botón compacto para las tarjetas del catálogo.
export function BotonAgregar({ p }: { p: P }) {
  const item = useLista().find((x) => x.codigo === p.codigo);
  if (item) {
    return (
      <Link href="/presupuesto"
        className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-[var(--primary)]/30 bg-[var(--primary)]/5 px-2 py-2 text-xs font-semibold text-[var(--primary)]">
        ✓ En tu lista ({item.cant})
      </Link>
    );
  }
  return (
    <button type="button" onClick={() => agregar(p)}
      className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-[var(--primary)] px-2 py-2 text-xs font-semibold text-[var(--primary)] hover:bg-[var(--primary)] hover:text-white">
      + Agregar a la lista
    </button>
  );
}

// Versión con cantidad para la ficha de producto.
export function AgregarConCantidad({ p }: { p: P }) {
  const [cant, setCant] = useState(1);
  const [ok, setOk] = useState(false);
  const item = useLista().find((x) => x.codigo === p.codigo);
  const acotar = (n: number) => Math.min(MAX_CANT, Math.max(1, Math.floor(n) || 1));
  const fijar = (n: number) => setCant(acotar(n));
  const sumar = (d: number) => setCant((c) => acotar(c + d)); // funcional: toques rápidos no se pierden

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2">
        <div className="flex items-center rounded-lg border border-[var(--outline-variant)] bg-white">
          <button type="button" aria-label="Restar" onClick={() => sumar(-1)} className="h-12 w-10 text-lg text-[var(--primary)]">−</button>
          <input aria-label="Cantidad" inputMode="numeric" value={cant}
            onChange={(e) => fijar(Number(e.target.value.replace(/\D/g, "")))}
            className="h-12 w-14 border-x border-[var(--outline-variant)] text-center text-sm focus:outline-none" />
          <button type="button" aria-label="Sumar" onClick={() => sumar(1)} className="h-12 w-10 text-lg text-[var(--primary)]">+</button>
        </div>
        <button type="button"
          onClick={() => { agregar(p, cant); setOk(true); setCant(1); }}
          className="h-12 flex-1 rounded-lg bg-[var(--primary)] px-4 text-sm font-semibold text-white hover:brightness-110">
          Agregar a la lista
        </button>
      </div>
      {p.bulto && (
        <p className="text-xs text-[var(--on-surface-variant)]">
          {cant} {textoBulto(p.bulto, cant)} = <strong>{(cant * p.bulto.cantidad).toLocaleString("es-AR")} {p.bulto.unidad}</strong>
        </p>
      )}
      {(ok || item) && (
        <p className="text-xs text-[var(--on-surface-variant)]" role="status">
          {item ? <>Tenés {item.cant}{item.bulto ? ` ${textoBulto(item.bulto, item.cant)}` : ""} en tu lista. </> : null}
          <Link href="/presupuesto" className="font-semibold text-[var(--primary)] underline">Ver lista y pedir cotización</Link>
        </p>
      )}
    </div>
  );
}

// Acceso a la lista en el menú: solo aparece cuando hay algo.
export function IndicadorLista({ onClick }: { onClick?: () => void }) {
  const n = useLista().length;
  if (!n) return null;
  return (
    <Link href="/presupuesto" onClick={onClick} aria-label={`Mi lista para presupuestar: ${n} productos`}
      className="relative flex items-center gap-2 rounded-lg border border-[var(--primary)]/40 px-3 py-2 text-xs font-semibold text-[var(--primary)] hover:bg-[var(--primary)]/5">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
        <path d="M9 5h11M9 12h11M9 19h11M4 5h.01M4 12h.01M4 19h.01" strokeLinecap="round" />
      </svg>
      <span className="hidden sm:inline">Mi lista</span>
      <span className="rounded-full bg-[var(--secondary)] px-1.5 py-0.5 text-[10px] leading-none text-white">{n}</span>
    </Link>
  );
}
