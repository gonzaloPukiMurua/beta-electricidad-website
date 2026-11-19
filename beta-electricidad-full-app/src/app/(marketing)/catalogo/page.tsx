import type { Metadata } from "next";
import Link from "next/link";
import { categorias, filtrar, obtenerCatalogo, type Filtros } from "@/lib/catalogo";
import { TarjetaProducto } from "@/components/catalogo/TarjetaProducto";
import { WA_NUMBER } from "@/lib/constants/whatsApp";

const POR_PAGINA = 24;

type Props = { searchParams: Promise<{ [k: string]: string | string[] | undefined }> };

const uno = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v)?.trim() || undefined;

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const sp = await searchParams;
  const sub = uno(sp.sub), cat = uno(sp.categoria);
  const titulo = sub ?? cat ?? "Catálogo";
  return {
    title: titulo,
    description: `${titulo}: materiales eléctricos e iluminación en Beta Electricidad, La Falda, Córdoba. Consultá disponibilidad por WhatsApp.`,
    alternates: { canonical: "/catalogo" + (cat ? `?categoria=${encodeURIComponent(cat)}${sub ? `&sub=${encodeURIComponent(sub)}` : ""}` : "") },
  };
}

function enlace(f: Filtros & { pagina?: number }) {
  const p = new URLSearchParams();
  if (f.categoria) p.set("categoria", f.categoria);
  if (f.sub) p.set("sub", f.sub);
  if (f.q) p.set("q", f.q);
  if (f.disponibles) p.set("disp", "1");
  if (f.pagina && f.pagina > 1) p.set("pagina", String(f.pagina));
  const s = p.toString();
  return s ? `/catalogo?${s}` : "/catalogo";
}

export default async function CatalogoPage({ searchParams }: Props) {
  const sp = await searchParams;
  const filtros: Filtros = {
    categoria: uno(sp.categoria),
    sub: uno(sp.sub),
    q: uno(sp.q)?.slice(0, 80),
    disponibles: uno(sp.disp) === "1",
  };
  const todos = await obtenerCatalogo();
  const arbol = categorias(todos);
  const resultado = filtrar(todos, filtros);
  const paginas = Math.max(1, Math.ceil(resultado.length / POR_PAGINA));
  const pagina = Math.min(paginas, Math.max(1, Number(uno(sp.pagina)) || 1));
  const visibles = resultado.slice((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA);
  const catActual = arbol.find((c) => c.nombre === filtros.categoria);

  const titulo = filtros.sub ?? filtros.categoria ?? "Catálogo";
  const waTexto = encodeURIComponent(
    filtros.q ? `Hola, busco: ${filtros.q}. ¿Lo tienen?` : "Hola, quisiera consultar por un producto.",
  );

  return (
    <main className="mx-auto max-w-[1280px] px-4 pb-24 pt-28 md:px-10">
      {/* Encabezado y búsqueda */}
      <nav aria-label="Ruta" className="mb-2 text-xs text-[var(--on-surface-variant)]">
        <Link href="/catalogo" className="hover:text-[var(--primary)]">Catálogo</Link>
        {filtros.categoria && (<> / <Link href={enlace({ categoria: filtros.categoria })} className="hover:text-[var(--primary)]">{filtros.categoria}</Link></>)}
        {filtros.sub && <> / <span>{filtros.sub}</span></>}
      </nav>
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[var(--primary)]">{titulo}</h1>
          <p className="mt-1 text-sm text-[var(--on-surface-variant)]">
            {resultado.length} {resultado.length === 1 ? "producto" : "productos"}
            {filtros.q ? <> para “{filtros.q}”</> : null}
          </p>
        </div>
        <form action="/catalogo" method="get" role="search" className="flex w-full gap-2 md:w-[420px]">
          {filtros.categoria && <input type="hidden" name="categoria" value={filtros.categoria} />}
          {filtros.sub && <input type="hidden" name="sub" value={filtros.sub} />}
          {filtros.disponibles && <input type="hidden" name="disp" value="1" />}
          <label htmlFor="q" className="sr-only">Buscar productos</label>
          <input
            id="q" name="q" type="search" defaultValue={filtros.q ?? ""}
            placeholder="Buscar por nombre, marca o código"
            className="min-w-0 flex-1 rounded-lg border border-[var(--outline-variant)] bg-white px-3 py-2.5 text-sm focus:border-[var(--primary)] focus:outline-none"
          />
          <button className="rounded-lg bg-[var(--primary)] px-4 text-sm font-semibold text-white hover:brightness-110">Buscar</button>
        </form>
      </div>

      <div className="grid gap-8 md:grid-cols-[240px_1fr]">
        {/* Categorías */}
        <aside aria-label="Categorías" className="md:sticky md:top-28 md:self-start">
          {/* Móvil: chips con scroll horizontal */}
          <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-2 md:hidden">
            <Chip href={enlace({ q: filtros.q, disponibles: filtros.disponibles })} activo={!filtros.categoria}>Todo</Chip>
            {arbol.map((c) => (
              <Chip key={c.nombre} href={enlace({ categoria: c.nombre, q: filtros.q, disponibles: filtros.disponibles })} activo={filtros.categoria === c.nombre}>
                {c.nombre} <span className="opacity-60">{c.total}</span>
              </Chip>
            ))}
          </div>
          {catActual && catActual.subs.length > 1 && (
            <div className="-mx-4 mt-1 flex gap-2 overflow-x-auto px-4 pb-2 md:hidden">
              {catActual.subs.map((s) => (
                <Chip key={s.nombre} chico href={enlace({ categoria: catActual.nombre, sub: s.nombre, q: filtros.q, disponibles: filtros.disponibles })} activo={filtros.sub === s.nombre}>
                  {s.nombre} <span className="opacity-60">{s.total}</span>
                </Chip>
              ))}
            </div>
          )}

          {/* Escritorio: lista */}
          <ul className="hidden space-y-1 text-sm md:block">
            <li>
              <Link href={enlace({ q: filtros.q, disponibles: filtros.disponibles })}
                className={`block rounded-md px-2 py-1.5 ${!filtros.categoria ? "bg-[var(--primary)]/10 font-semibold text-[var(--primary)]" : "hover:bg-black/5"}`}>
                Todo el catálogo <span className="text-[var(--on-surface-variant)]">({todos.length})</span>
              </Link>
            </li>
            {arbol.map((c) => (
              <li key={c.nombre}>
                <Link href={enlace({ categoria: c.nombre, q: filtros.q, disponibles: filtros.disponibles })}
                  className={`flex justify-between rounded-md px-2 py-1.5 ${filtros.categoria === c.nombre && !filtros.sub ? "bg-[var(--primary)]/10 font-semibold text-[var(--primary)]" : "hover:bg-black/5"}`}>
                  <span>{c.nombre}</span><span className="text-[var(--on-surface-variant)]">{c.total}</span>
                </Link>
                {filtros.categoria === c.nombre && c.subs.length > 1 && (
                  <ul className="ml-3 mt-1 space-y-0.5 border-l border-[var(--outline-variant)] pl-2">
                    {c.subs.map((s) => (
                      <li key={s.nombre}>
                        <Link href={enlace({ categoria: c.nombre, sub: s.nombre, q: filtros.q, disponibles: filtros.disponibles })}
                          className={`flex justify-between rounded px-2 py-1 text-[13px] ${filtros.sub === s.nombre ? "font-semibold text-[var(--primary)]" : "text-[var(--on-surface-variant)] hover:text-[var(--primary)]"}`}>
                          <span>{s.nombre}</span><span>{s.total}</span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>

          <Link
            href={enlace({ ...filtros, disponibles: !filtros.disponibles })}
            className="mt-3 inline-flex items-center gap-2 text-sm text-[var(--on-surface-variant)] hover:text-[var(--primary)] md:mt-5"
          >
            <span className={`flex h-4 w-4 items-center justify-center rounded border ${filtros.disponibles ? "border-[var(--primary)] bg-[var(--primary)] text-white" : "border-[var(--outline-variant)] bg-white"}`} aria-hidden="true">
              {filtros.disponibles ? "✓" : ""}
            </span>
            Solo disponibles hoy
          </Link>
        </aside>

        {/* Resultados */}
        <section aria-label="Productos">
          {visibles.length === 0 ? (
            <div className="rounded-xl border border-dashed border-[var(--outline-variant)] bg-white p-10 text-center">
              <p className="font-semibold text-[var(--on-surface)]">No encontramos productos con esa búsqueda.</p>
              <p className="mt-1 text-sm text-[var(--on-surface-variant)]">
                Publicamos una parte de lo que tenemos en el local. Escribinos y te decimos si lo tenemos.
              </p>
              <a href={`https://wa.me/${WA_NUMBER}?text=${waTexto}`} target="_blank" rel="noopener noreferrer"
                className="mt-4 inline-block rounded-lg bg-[var(--primary)] px-5 py-2.5 text-sm font-semibold text-white hover:brightness-110">
                Consultar por WhatsApp
              </a>
            </div>
          ) : (
            <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 md:gap-4">
              {visibles.map((p) => (<li key={p.codigo} className="flex"><TarjetaProducto p={p} /></li>))}
            </ul>
          )}

          {paginas > 1 && (
            <nav aria-label="Paginación" className="mt-8 flex items-center justify-center gap-2 text-sm">
              {pagina > 1 && <Link href={enlace({ ...filtros, pagina: pagina - 1 })} className="rounded-md border border-[var(--outline-variant)] bg-white px-3 py-2 hover:border-[var(--primary)]">← Anterior</Link>}
              <span className="px-2 text-[var(--on-surface-variant)]">Página {pagina} de {paginas}</span>
              {pagina < paginas && <Link href={enlace({ ...filtros, pagina: pagina + 1 })} className="rounded-md border border-[var(--outline-variant)] bg-white px-3 py-2 hover:border-[var(--primary)]">Siguiente →</Link>}
            </nav>
          )}

          <p className="mt-10 text-center text-xs text-[var(--on-surface-variant)]">
            ¿No encontrás lo que buscás? Tenemos mucho más en el local de La Falda.{" "}
            <a href={`https://wa.me/${WA_NUMBER}?text=${waTexto}`} target="_blank" rel="noopener noreferrer" className="font-semibold text-[var(--primary)] underline">Consultanos</a>.
          </p>
        </section>
      </div>
    </main>
  );
}

function Chip({ href, activo, chico, children }: { href: string; activo: boolean; chico?: boolean; children: React.ReactNode }) {
  return (
    <Link href={href}
      className={`shrink-0 whitespace-nowrap rounded-full border ${chico ? "px-3 py-1 text-xs" : "px-3.5 py-1.5 text-sm"} ${activo ? "border-[var(--primary)] bg-[var(--primary)] text-white" : "border-[var(--outline-variant)] bg-white text-[var(--on-surface)]"}`}>
      {children}
    </Link>
  );
}
