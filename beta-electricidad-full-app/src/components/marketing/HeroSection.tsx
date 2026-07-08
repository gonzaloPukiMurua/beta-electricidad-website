import Link from "next/link";
import { WA_NUMBER, WA_MESSAGE } from "@/lib/constants/whatsApp";

export function HeroSection() {
  return (
    <section className="min-h-[90vh] flex flex-col justify-center bg-[var(--brand-secondary)] text-white px-6 py-20">
      <div className="max-w-3xl mx-auto text-center">
        <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6">
          Materiales eléctricos en La Falda
        </h1>
        <p className="text-lg md:text-xl text-white/80 mb-10">
          Stock disponible para electricistas, instaladores y constructoras.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href={`https://wa.me/${WA_NUMBER}?text=${WA_MESSAGE}`}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full bg-[var(--brand-accent)] px-8 py-4 font-semibold text-white hover:brightness-110 transition-all"
          >
            Consultar por WhatsApp
          </a>
          <a
            href="tel:+5493548575510"
            className="rounded-full border border-white/40 px-8 py-4 font-semibold text-white hover:bg-white/10 transition-all"
          >
            Llamanos
          </a>
        </div>
      </div>
    </section>
  );
}