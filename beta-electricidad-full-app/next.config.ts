import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Hosting compartido (Hostinger) limita procesos y memoria: un solo worker
  // al generar páginas. El build usa webpack (`next build --webpack`) porque
  // Turbopack no logra lanzar su proceso de PostCSS en ese entorno.
  experimental: {
    cpus: 1,
  },
};

export default nextConfig;
