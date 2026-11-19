"use client";

import { useState } from "react";
import { IconoProducto } from "./IconoProducto";

// Foto del producto (por ahora, la URL del fabricante). Si no hay o no carga,
// muestra el ícono de la subcategoría con la leyenda "Imagen ilustrativa".
export function ImagenProducto({ src, alt, categoria, subcategoria, grande = false }: {
  src: string | null;
  alt: string;
  categoria: string | null;
  subcategoria: string | null;
  grande?: boolean;
}) {
  const [fallo, setFallo] = useState(false);

  if (src && !fallo) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- imágenes externas de fabricantes; se migran a almacenamiento propio más adelante
      <img
        src={src}
        alt={alt}
        loading={grande ? "eager" : "lazy"}
        referrerPolicy="no-referrer"
        onError={() => setFallo(true)}
        className="h-full w-full object-contain p-3"
      />
    );
  }
  return (
    <div className="relative flex h-full w-full items-center justify-center text-[var(--primary)]/70">
      <IconoProducto categoria={categoria} subcategoria={subcategoria} className={grande ? "h-32 w-32" : "h-16 w-16"} />
      <span className="absolute bottom-2 left-2 rounded bg-white/90 px-1.5 py-0.5 text-[10px] text-[var(--on-surface-variant)]">
        Imagen ilustrativa
      </span>
    </div>
  );
}
