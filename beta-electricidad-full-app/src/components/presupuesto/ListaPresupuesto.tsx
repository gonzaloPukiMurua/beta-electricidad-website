"use client";

import { useState } from "react";
import Link from "next/link";
import { cambiarCantidad, mensajeLista, quitar, useLista, vaciar, MAX_CANT } from "@/lib/presupuesto";
import { EMAIL_CONTACTO, WA_NUMBER } from "@/lib/constants/whatsApp";
import { textoBulto } from "@/lib/catalogo";

export function ListaPresupuesto() {
  const lista = useLista();
  const [datos, setDatos] = useState({ nombre: "", localidad: "", notas: "" });
  const [confirmarVaciar, setConfirmarVaciar] = useState(false);

  if (lista.length === 0) {
    return (
      <div className="mt-8 rounded-xl border border-dashed border-[var(--outline-variant)] bg-white p-10 text-center">
        <p className="font-semibold text-[var(--on-surface)]">Tu lista está vacía.</p>
        <p className="mt-1 text-sm text-[var(--on-surface-variant)]">
          En el catálogo, tocá “Agregar a la lista” en cada producto que necesites.
        </p>
        <Link href="/catalogo" className="mt-4 inline-block rounded-lg bg-[var(--primary)] px-5 py-2.5 text-sm font-semibold text-white hover:brightness-110">
          Ir al catálogo
        </Link>
      </div>
    );
  }

  const texto = mensajeLista(lista, datos);
  const wa = `https://wa.me/${WA_NUMBER}?text=${encodeURIComponent(texto)}`;
  const mail = `mailto:${EMAIL_CONTACTO}?subject=${encodeURIComponent("Pedido de cotización")}&body=${encodeURIComponent(texto)}`;
  const campo = "w-full rounded-lg border border-[var(--outline-variant)] bg-white px-3 py-2.5 text-sm focus:border-[var(--primary)] focus:outline-none";

  return (
    <div className="mt-6 flex flex-col gap-6">
      <ul className="divide-y divide-[var(--outline-variant)]/50 rounded-xl border border-[var(--outline-variant)]/60 bg-white">
        {lista.map((x) => (
          <li key={x.codigo} className="flex flex-wrap items-center gap-3 p-3 sm:flex-nowrap">
            <div className="min-w-0 flex-1 basis-full sm:basis-auto">
              <Link href={`/producto/${x.slug}`} className="break-words text-sm font-medium text-[var(--on-surface)] hover:text-[var(--primary)]">
                {x.nombre}
              </Link>
              <p className="font-mono text-[11px] text-[var(--on-surface-variant)]">Cód. {x.codigo}</p>
              {x.bulto && (
                <p className="text-xs text-[var(--primary)]">
                  {x.cant} {textoBulto(x.bulto, x.cant)} = {(x.cant * x.bulto.cantidad).toLocaleString("es-AR")} {x.bulto.unidad}
                </p>
              )}
            </div>
            <div className="flex items-center rounded-lg border border-[var(--outline-variant)]">
              <button type="button" aria-label={`Restar ${x.nombre}`} onClick={() => cambiarCantidad(x.codigo, x.cant - 1)}
                disabled={x.cant <= 1} className="h-10 w-9 text-lg text-[var(--primary)] disabled:opacity-30">−</button>
              <input aria-label={`Cantidad de ${x.nombre}`} inputMode="numeric" value={x.cant}
                onChange={(e) => cambiarCantidad(x.codigo, Number(e.target.value.replace(/\D/g, "")) || 1)}
                className="h-10 w-14 border-x border-[var(--outline-variant)] text-center text-sm focus:outline-none" />
              <button type="button" aria-label={`Sumar ${x.nombre}`} onClick={() => cambiarCantidad(x.codigo, x.cant + 1)}
                disabled={x.cant >= MAX_CANT} className="h-10 w-9 text-lg text-[var(--primary)] disabled:opacity-30">+</button>
            </div>
            <button type="button" onClick={() => quitar(x.codigo)} className="ml-auto text-xs text-[var(--on-surface-variant)] underline hover:text-[var(--secondary)] sm:ml-0">
              Quitar
            </button>
          </li>
        ))}
      </ul>

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-[var(--on-surface-variant)]">
        <span>{lista.length} {lista.length === 1 ? "producto" : "productos"}</span>
        <div className="flex gap-4">
          <Link href="/catalogo" className="font-semibold text-[var(--primary)] underline">Seguir agregando</Link>
          {confirmarVaciar ? (
            <span>
              ¿Vaciar la lista?{" "}
              <button type="button" onClick={() => { vaciar(); setConfirmarVaciar(false); }} className="font-semibold text-[var(--secondary)] underline">Sí</button>{" "}
              <button type="button" onClick={() => setConfirmarVaciar(false)} className="underline">No</button>
            </span>
          ) : (
            <button type="button" onClick={() => setConfirmarVaciar(true)} className="underline">Vaciar</button>
          )}
        </div>
      </div>

      <section aria-label="Tus datos" className="grid gap-3 rounded-xl border border-[var(--outline-variant)]/60 bg-white p-4 sm:grid-cols-2">
        <p className="text-sm font-semibold text-[var(--on-surface)] sm:col-span-2">
          Datos opcionales <span className="font-normal text-[var(--on-surface-variant)]">(van en el mensaje, no se guardan en el sitio)</span>
        </p>
        <input className={campo} placeholder="Tu nombre" autoComplete="name" maxLength={60}
          value={datos.nombre} onChange={(e) => setDatos({ ...datos, nombre: e.target.value })} />
        <input className={campo} placeholder="Localidad" autoComplete="address-level2" maxLength={60}
          value={datos.localidad} onChange={(e) => setDatos({ ...datos, localidad: e.target.value })} />
        <textarea className={`${campo} sm:col-span-2`} rows={2} placeholder="Notas: obra, medidas, si sos instalador, forma de pago…" maxLength={300}
          value={datos.notas} onChange={(e) => setDatos({ ...datos, notas: e.target.value })} />
      </section>

      <div className="flex flex-col gap-2 sm:flex-row">
        <a href={wa} target="_blank" rel="noopener noreferrer"
          className="flex flex-1 items-center justify-center rounded-lg bg-[#25D366] px-6 py-3.5 font-semibold text-white hover:brightness-105">
          Pedir cotización por WhatsApp
        </a>
        <a href={mail}
          className="flex items-center justify-center rounded-lg border border-[var(--primary)] px-6 py-3.5 text-sm font-semibold text-[var(--primary)] hover:bg-[var(--primary)]/5">
          Enviar por email
        </a>
      </div>

      <details className="text-sm text-[var(--on-surface-variant)]">
        <summary className="cursor-pointer">Ver el mensaje que se envía</summary>
        <pre className="mt-2 whitespace-pre-wrap break-words rounded-lg bg-[#f3f4f8] p-3 font-mono text-xs">{texto}</pre>
      </details>

      <p className="text-xs text-[var(--on-surface-variant)]">
        La lista queda guardada en este dispositivo. ¿Sos electricista o instalador? Contanos en las notas.
        ¿Comprás para una obra o en cantidad? Tenemos condiciones especiales por volumen.
      </p>
    </div>
  );
}
