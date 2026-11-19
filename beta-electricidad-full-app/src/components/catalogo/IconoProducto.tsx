// Íconos ilustrativos por subcategoría, para productos sin foto
// (o cuando la foto del fabricante no carga).

const TRAZO = { fill: "none", stroke: "currentColor", strokeWidth: 2.5, strokeLinejoin: "round" as const, strokeLinecap: "round" as const };

const ICONOS: Record<string, React.ReactNode> = {
  lampara: (<><path d="M32 8a16 16 0 0 0-9 29c2 1.6 3 3.6 3 6v3h12v-3c0-2.4 1-4.4 3-6A16 16 0 0 0 32 8Z" /><path d="M26 50h12M27 55h10M29 60h6" /></>),
  tubo: (<><rect x="6" y="27" width="52" height="10" rx="5" /><path d="M2 30v4M62 30v4M14 32h36" strokeDasharray="3 4" /></>),
  spot: (<><circle cx="32" cy="32" r="22" /><circle cx="32" cy="32" r="12" /><circle cx="32" cy="32" r="4" fill="currentColor" /></>),
  plafon: (<><path d="M8 22h48" /><path d="M12 22c0 12 9 20 20 20s20-8 20-20" /><path d="M24 48l-3 6M32 50v7M40 48l3 6" /></>),
  aplique: (<><rect x="8" y="14" width="10" height="36" rx="2" /><path d="M18 26h10l12-8v28l-12-8H18" /><path d="M46 24l8-4M47 32h9M46 40l8 4" /></>),
  colgante: (<><path d="M32 4v18" /><path d="M14 44c0-10 8-18 18-18s18 8 18 18Z" /><path d="M26 50c0 3 3 6 6 6s6-3 6-6" /></>),
  farol: (<><path d="M24 10h16l4 8H20Z" /><rect x="20" y="18" width="24" height="30" rx="2" /><path d="M32 26v14M18 48h28M32 4v6" /></>),
  proyector: (<><rect x="10" y="14" width="44" height="30" rx="3" /><path d="M16 20h32M16 26h32M16 32h32M16 38h32" strokeWidth={1.5} /><path d="M32 44v8M22 56h20" /></>),
  cinta: (<><path d="M4 40c10-18 20-18 28 0s18 18 28 0" /><g fill="currentColor"><circle cx="10" cy="31" r="2.5" /><circle cx="22" cy="25" r="2.5" /><circle cx="42" cy="47" r="2.5" /><circle cx="54" cy="41" r="2.5" /></g></>),
  emergencia: (<><rect x="8" y="22" width="48" height="20" rx="4" /><path d="M30 26l-4 8h8l-4 8" /><path d="M16 50h32" /></>),
  sensor: (<><circle cx="32" cy="36" r="14" /><path d="M20 14c7-5 17-5 24 0M14 8c11-8 25-8 36 0" /><circle cx="32" cy="36" r="4" fill="currentColor" /></>),
  portalampara: (<><path d="M24 8h16v14H24Z" /><path d="M20 22h24l-3 14H23Z" /><path d="M26 36h12v8H26ZM28 44v12M36 44v12" /></>),
  toma: (<><rect x="12" y="8" width="40" height="48" rx="6" /><circle cx="32" cy="32" r="11" /><path d="M28 29v5M36 29v5M32 37v3" /></>),
  llave: (<><rect x="12" y="8" width="40" height="48" rx="6" /><rect x="24" y="18" width="16" height="28" rx="3" /><path d="M24 32h16" /></>),
  cable: (<><ellipse cx="32" cy="32" rx="22" ry="22" /><ellipse cx="32" cy="32" rx="12" ry="12" /><path d="M54 32h8" /><path d="M10 32a22 22 0 0 1 3-11M18 50a22 22 0 0 0 8 4" /></>),
  caja: (<><rect x="10" y="12" width="44" height="40" rx="4" /><circle cx="22" cy="24" r="3" /><circle cx="42" cy="24" r="3" /><circle cx="22" cy="40" r="3" /><circle cx="42" cy="40" r="3" /></>),
  tablero: (<><rect x="12" y="6" width="40" height="52" rx="3" /><path d="M18 22h28M18 38h28" /><path d="M22 26v8M28 26v8M34 26v8M40 26v8" /></>),
  pilar: (<><path d="M20 58V18h24v40" /><rect x="24" y="24" width="16" height="12" rx="1" /><path d="M14 58h36M32 4v14" /></>),
  cano: (<><path d="M6 26h32a12 12 0 0 1 12 12v20" /><path d="M6 38h32v20" /><path d="M6 22v20M34 58h20" /></>),
  proteccion: (<><rect x="18" y="6" width="28" height="52" rx="3" /><rect x="26" y="18" width="12" height="16" rx="2" /><path d="M32 22v8M24 44h16M24 50h16" /></>),
  cinta_aisladora: (<><circle cx="32" cy="32" r="22" /><circle cx="32" cy="32" r="10" /><path d="M54 32h6v14" /></>),
  herramienta: (<><path d="M40 8a12 12 0 0 0-11 16L8 45l11 11 21-21a12 12 0 0 0 16-11l-7 4-6-6 4-7Z" /></>),
  generico: (<><path d="M36 4 14 36h16l-4 24 24-34H34Z" /></>),
};

const POR_SUBCATEGORIA: Record<string, keyof typeof ICONOS> = {
  "Lámparas": "lampara", "Spots y embutidos": "spot", "Plafones": "plafon", "Apliques": "aplique",
  "Colgantes": "colgante", "Faroles": "farol", "Proyectores": "proyector", "Cintas LED y fuentes": "cinta",
  "Emergencia": "emergencia", "Fotocontroles y sensores": "sensor", "Portalámparas y accesorios": "portalampara",
  "Artefactos para tubos": "tubo", "Tortugas": "plafon",
  "Llaves y tomas": "toma", "Llaves armadas": "llave", "Exterior": "toma", "Fichas y adaptadores": "toma",
  "Cajas de embutir": "caja", "Cajas de paso": "caja", "Tableros": "tablero", "Gabinetes": "tablero",
  "Cajas para medidor": "pilar", "Pilares y medidores": "pilar", "Accesorios para cajas y tableros": "caja",
  "Caños": "cano", "Accesorios de cañería": "cano", "Fijación": "cano", "Cablecanal": "cano",
  "Cintas aisladoras": "cinta_aisladora", "Herramientas": "herramienta",
};
const POR_CATEGORIA: Record<string, keyof typeof ICONOS> = {
  "Iluminación": "lampara", "Llaves y tomas": "llave", "Cables": "cable", "Cajas y tableros": "tablero",
  "Cañerías y accesorios": "cano", "Protecciones": "proteccion",
};

export function IconoProducto({ categoria, subcategoria, className }: {
  categoria: string | null; subcategoria: string | null; className?: string;
}) {
  const clave = (subcategoria && POR_SUBCATEGORIA[subcategoria]) || (categoria && POR_CATEGORIA[categoria]) || "generico";
  return (
    <svg viewBox="0 0 64 64" {...TRAZO} className={className} aria-hidden="true">
      {ICONOS[clave]}
    </svg>
  );
}
