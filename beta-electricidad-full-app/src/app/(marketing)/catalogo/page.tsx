import type { Metadata } from "next";
import { WA_NUMBER } from "@/lib/constants/whatsApp";

export const metadata: Metadata = {
  title: "Catálogo",
  description: "Catálogo de iluminación, llaves y materiales eléctricos de Beta Electricidad.",
};

// F1: este marcador se reemplaza por el catálogo real, que lee la vista
// `catalogo_publico` de Supabase.
export default function CatalogoPage() {
  const mensaje = encodeURIComponent("Hola, quisiera consultar por productos del catálogo.");
  return (
    <main className="mx-auto flex min-h-[70vh] max-w-2xl flex-col justify-center gap-4 px-4 py-24">
      <p className="text-sm font-semibold uppercase tracking-wide text-[var(--secondary)]">Catálogo</p>
      <h1 className="text-3xl font-bold text-[var(--primary)]">Estamos preparando el catálogo online</h1>
      <p className="text-[var(--on-surface-variant)]">
        Mientras tanto, consultanos por WhatsApp qué necesitás y te respondemos con disponibilidad y presupuesto.
      </p>
      <a
        href={`https://wa.me/${WA_NUMBER}?text=${mensaje}`}
        target="_blank"
        rel="noopener noreferrer"
        className="w-fit rounded-md bg-[var(--primary)] px-5 py-3 font-semibold text-white hover:brightness-110"
      >
        Consultar por WhatsApp
      </a>
    </main>
  );
}
