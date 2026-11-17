import type { MetadataRoute } from "next";

// Solo producción se indexa. En el entorno de prueba (subdominio) no se define
// NEXT_PUBLIC_INDEXAR y los buscadores no lo indexan.
export default function robots(): MetadataRoute.Robots {
  if (process.env.NEXT_PUBLIC_INDEXAR !== "true") {
    return { rules: { userAgent: "*", disallow: "/" } };
  }
  const site = process.env.NEXT_PUBLIC_SITE_URL ?? "https://betaelectricidad.com.ar";
  return { rules: { userAgent: "*", allow: "/" }, sitemap: `${site}/sitemap.xml` };
}
