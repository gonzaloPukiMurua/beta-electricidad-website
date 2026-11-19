// Acceso al catálogo público. Lee SOLO la vista `catalogo_publico` con la
// clave pública (ver supabase/migrations). Corre en el servidor.

export type Producto = {
  codigo: number;
  codigo_fabrica: string | null;
  nombre: string;
  marca: string | null;
  rubro: string | null;
  categoria_web: string | null;
  subcategoria_web: string | null;
  descripcion: string | null;
  destacado: boolean;
  orden: number | null;
  disponible: boolean;
  precio_un_pago: number | null;
  imagen_url: string | null;
};

export type Categoria = { nombre: string; total: number; subs: { nombre: string; total: number }[] };

// Orden de navegación; lo que no esté acá va al final, alfabético.
const ORDEN_CATEGORIAS = [
  "Iluminación", "Llaves y tomas", "Cables", "Cajas y tableros",
  "Cañerías y accesorios", "Protecciones", "Otros",
];

const REVALIDAR_SEGUNDOS = 3600; // la sincronización del ERP corre 2 veces por día

export async function obtenerCatalogo(): Promise<Producto[]> {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) throw new Error("Faltan NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY");

  const productos: Producto[] = [];
  const pagina = 1000;
  for (let desde = 0; ; desde += pagina) {
    const res = await fetch(`${url}/rest/v1/catalogo_publico?select=*&order=codigo`, {
      headers: { apikey: key, Authorization: `Bearer ${key}`, Range: `${desde}-${desde + pagina - 1}` },
      // Explícito: sin esto, un fetch posterior a leer searchParams no se cachea.
      cache: "force-cache",
      next: { revalidate: REVALIDAR_SEGUNDOS, tags: ["catalogo"] },
    });
    if (!res.ok) throw new Error(`Catálogo: HTTP ${res.status}`);
    const lote = (await res.json()) as Producto[];
    productos.push(...lote);
    if (lote.length < pagina) break;
  }
  return productos.sort(compararProductos);
}

export async function obtenerProducto(codigo: number): Promise<Producto | undefined> {
  return (await obtenerCatalogo()).find((p) => p.codigo === codigo);
}

// Destacados primero, luego orden manual, luego disponibles, luego nombre.
function compararProductos(a: Producto, b: Producto): number {
  return (
    Number(b.destacado) - Number(a.destacado) ||
    (a.orden ?? 1e9) - (b.orden ?? 1e9) ||
    Number(b.disponible) - Number(a.disponible) ||
    a.nombre.localeCompare(b.nombre, "es")
  );
}

export function normalizar(s: string): string {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

export function slugProducto(p: Pick<Producto, "codigo" | "nombre">): string {
  const base = normalizar(p.nombre).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 80);
  return `${p.codigo}-${base}`;
}

export function codigoDesdeSlug(slug: string): number | null {
  const m = /^(\d+)/.exec(slug);
  return m ? Number(m[1]) : null;
}

export function categorias(productos: Producto[]): Categoria[] {
  const mapa = new Map<string, Map<string, number>>();
  for (const p of productos) {
    const cat = p.categoria_web ?? "Otros";
    const sub = p.subcategoria_web ?? "Varios";
    const subs = mapa.get(cat) ?? new Map<string, number>();
    subs.set(sub, (subs.get(sub) ?? 0) + 1);
    mapa.set(cat, subs);
  }
  const pos = (c: string) => {
    const i = ORDEN_CATEGORIAS.indexOf(c);
    return i === -1 ? 999 : i;
  };
  return [...mapa.entries()]
    .map(([nombre, subs]) => ({
      nombre,
      total: [...subs.values()].reduce((a, b) => a + b, 0),
      subs: [...subs.entries()]
        .map(([n, total]) => ({ nombre: n, total }))
        .sort((a, b) => b.total - a.total || a.nombre.localeCompare(b.nombre, "es")),
    }))
    .sort((a, b) => pos(a.nombre) - pos(b.nombre) || a.nombre.localeCompare(b.nombre, "es"));
}

export type Filtros = { categoria?: string; sub?: string; q?: string; disponibles?: boolean };

export function filtrar(productos: Producto[], f: Filtros): Producto[] {
  const palabras = f.q ? normalizar(f.q).split(/\s+/).filter(Boolean) : [];
  return productos.filter((p) => {
    if (f.categoria && (p.categoria_web ?? "Otros") !== f.categoria) return false;
    if (f.sub && (p.subcategoria_web ?? "Varios") !== f.sub) return false;
    if (f.disponibles && !p.disponible) return false;
    if (palabras.length) {
      const texto = normalizar(
        [p.nombre, p.marca, p.codigo, p.codigo_fabrica, p.subcategoria_web, p.rubro].filter(Boolean).join(" "),
      );
      return palabras.every((w) => texto.includes(w));
    }
    return true;
  });
}
