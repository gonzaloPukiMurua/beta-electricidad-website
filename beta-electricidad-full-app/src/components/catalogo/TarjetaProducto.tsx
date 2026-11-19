import Link from "next/link";
import { slugProducto, type Producto } from "@/lib/catalogo";
import { ImagenProducto } from "./ImagenProducto";
import { Disponibilidad } from "./Disponibilidad";

export function TarjetaProducto({ p }: { p: Producto }) {
  return (
    <Link
      href={`/producto/${slugProducto(p)}`}
      className="group flex flex-col overflow-hidden rounded-xl border border-[var(--outline-variant)]/60 bg-white transition-shadow hover:shadow-md focus-visible:outline-2 focus-visible:outline-[var(--primary)]"
    >
      <div className="aspect-square border-b border-[var(--outline-variant)]/40 bg-[#f3f4f8]">
        <ImagenProducto src={p.imagen_url} alt={p.nombre} categoria={p.categoria_web} subcategoria={p.subcategoria_web} />
      </div>
      <div className="flex flex-1 flex-col gap-1.5 p-3">
        {p.marca && <span className="text-[11px] font-semibold uppercase tracking-wide text-[var(--secondary)]">{p.marca}</span>}
        <h3 className="line-clamp-3 text-sm font-medium leading-snug text-[var(--on-surface)] group-hover:text-[var(--primary)]">
          {p.nombre}
        </h3>
        <span className="font-mono text-[11px] text-[var(--on-surface-variant)]">
          Cód. {p.codigo}{p.codigo_fabrica ? ` · ${p.codigo_fabrica}` : ""}
        </span>
        <div className="mt-auto pt-1">
          <Disponibilidad disponible={p.disponible} />
        </div>
      </div>
    </Link>
  );
}
