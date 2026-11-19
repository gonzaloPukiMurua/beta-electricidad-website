import type { Metadata } from "next";
import Link from "next/link";
import { notFound, permanentRedirect } from "next/navigation";
import { codigoDesdeSlug, obtenerCatalogo, obtenerProducto, slugProducto } from "@/lib/catalogo";
import { ImagenProducto } from "@/components/catalogo/ImagenProducto";
import { Disponibilidad } from "@/components/catalogo/Disponibilidad";
import { TarjetaProducto } from "@/components/catalogo/TarjetaProducto";
import { WA_NUMBER } from "@/lib/constants/whatsApp";

type Props = { params: Promise<{ slug: string }> };

async function cargar(slug: string) {
  const codigo = codigoDesdeSlug(slug);
  return codigo === null ? undefined : obtenerProducto(codigo);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const p = await cargar((await params).slug);
  if (!p) return { title: "Producto no encontrado" };
  const desc = `${p.nombre}${p.marca ? ` (${p.marca})` : ""}. ${p.disponible ? "Disponible" : "Consultá disponibilidad"} en Beta Electricidad, La Falda, Córdoba.`;
  return {
    title: p.nombre,
    description: desc,
    alternates: { canonical: `/producto/${slugProducto(p)}` },
    openGraph: { title: p.nombre, description: desc, images: p.imagen_url ? [p.imagen_url] : undefined },
  };
}

export default async function ProductoPage({ params }: Props) {
  const { slug } = await params;
  const p = await cargar(slug);
  if (!p) notFound();
  if (slug !== slugProducto(p)) permanentRedirect(`/producto/${slugProducto(p)}`);

  const mensaje = encodeURIComponent(
    `Hola, quisiera consultar por este producto:\n${p.nombre}\nCódigo: ${p.codigo}${p.codigo_fabrica ? ` (fábrica ${p.codigo_fabrica})` : ""}`,
  );
  const relacionados = (await obtenerCatalogo())
    .filter((x) => x.codigo !== p.codigo && x.subcategoria_web === p.subcategoria_web && x.categoria_web === p.categoria_web)
    .slice(0, 4);
  const urlCategoria = p.categoria_web ? `/catalogo?categoria=${encodeURIComponent(p.categoria_web)}` : "/catalogo";

  return (
    <main className="mx-auto max-w-[1280px] px-4 pb-24 pt-28 md:px-10">
      <nav aria-label="Ruta" className="mb-4 text-xs text-[var(--on-surface-variant)]">
        <Link href="/catalogo" className="hover:text-[var(--primary)]">Catálogo</Link>
        {p.categoria_web && <> / <Link href={urlCategoria} className="hover:text-[var(--primary)]">{p.categoria_web}</Link></>}
        {p.subcategoria_web && <> / <Link href={`${urlCategoria}&sub=${encodeURIComponent(p.subcategoria_web)}`} className="hover:text-[var(--primary)]">{p.subcategoria_web}</Link></>}
      </nav>

      <div className="grid gap-8 md:grid-cols-2 md:gap-12">
        <div className="aspect-square overflow-hidden rounded-2xl border border-[var(--outline-variant)]/60 bg-[#f3f4f8]">
          <ImagenProducto src={p.imagen_url} alt={p.nombre} categoria={p.categoria_web} subcategoria={p.subcategoria_web} grande />
        </div>

        <div className="flex flex-col gap-4">
          {p.marca && <span className="text-xs font-semibold uppercase tracking-wide text-[var(--secondary)]">{p.marca}</span>}
          <h1 className="text-2xl font-bold leading-tight text-[var(--on-surface)] md:text-3xl">{p.nombre}</h1>
          <Disponibilidad disponible={p.disponible} />

          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 rounded-xl border border-[var(--outline-variant)]/60 bg-white p-4 text-sm">
            <dt className="text-[var(--on-surface-variant)]">Código</dt><dd className="font-mono">{p.codigo}</dd>
            {p.codigo_fabrica && (<><dt className="text-[var(--on-surface-variant)]">Cód. fábrica</dt><dd className="font-mono">{p.codigo_fabrica}</dd></>)}
            {p.marca && (<><dt className="text-[var(--on-surface-variant)]">Marca</dt><dd>{p.marca}</dd></>)}
            {p.subcategoria_web && (<><dt className="text-[var(--on-surface-variant)]">Categoría</dt><dd>{p.categoria_web} · {p.subcategoria_web}</dd></>)}
          </dl>

          {p.descripcion && <p className="whitespace-pre-line text-sm leading-relaxed text-[var(--on-surface-variant)]">{p.descripcion}</p>}

          <a
            href={`https://wa.me/${WA_NUMBER}?text=${mensaje}`}
            target="_blank" rel="noopener noreferrer"
            className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-[#25D366] px-6 py-3.5 font-semibold text-white hover:brightness-105 md:w-fit"
          >
            Consultar precio y disponibilidad por WhatsApp
          </a>
          <p className="text-xs text-[var(--on-surface-variant)]">
            Te respondemos con el precio del día. Si sos instalador o comprás por cantidad, avisanos.
            {p.imagen_url ? " La imagen es del fabricante y puede variar." : ""}
          </p>
        </div>
      </div>

      {relacionados.length > 0 && (
        <section className="mt-16" aria-label="Productos relacionados">
          <h2 className="mb-4 text-lg font-bold text-[var(--primary)]">Más en {p.subcategoria_web ?? p.categoria_web}</h2>
          <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 md:gap-4">
            {relacionados.map((r) => (<li key={r.codigo} className="flex"><TarjetaProducto p={r} /></li>))}
          </ul>
        </section>
      )}
    </main>
  );
}
