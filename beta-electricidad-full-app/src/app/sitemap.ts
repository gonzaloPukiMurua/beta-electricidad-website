import type { MetadataRoute } from "next";
import { obtenerCatalogo, slugProducto } from "@/lib/catalogo";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "https://betaelectricidad.com.ar";

export const revalidate = 3600;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const productos = await obtenerCatalogo();
  return [
    { url: `${SITE}/`, changeFrequency: "weekly", priority: 1 },
    { url: `${SITE}/catalogo`, changeFrequency: "daily", priority: 0.9 },
    ...productos.map((p) => ({ url: `${SITE}/producto/${slugProducto(p)}`, changeFrequency: "weekly" as const, priority: 0.6 })),
  ];
}
