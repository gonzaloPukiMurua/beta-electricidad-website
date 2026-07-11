import { Button } from "@/components/ui/Button";
import { WA_NUMBER, WA_MESSAGE } from "@/lib/constants/whatsApp";

const STATS = [
  { value: "34+", label: "Años de trayectoria" },
  { value: "Full", label: "Mayorista / Minorista" },
  { value: "12k+", label: "Productos en stock" },
  { value: "Top", label: "Asesoramiento técnico" },
];

export function HeroSection() {
  return (
    <section
      id="inicio"
      className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden bg-[var(--primary)]"
    >
      {/* Placeholder imagen de fondo — reemplazar con Next/Image en producción */}
      <div className="absolute inset-0 -z-10 bg-[var(--primary)]" aria-hidden="true">
        {/* <Image src="/hero-bg.jpg" alt="" fill className="object-cover opacity-20" /> */}
      </div>

      <div className="max-w-[1280px] mx-auto px-4 md:px-10 relative z-10 text-center">
        <div className="max-w-3xl mx-auto space-y-8">

          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 text-white rounded-full text-xs font-semibold uppercase tracking-wider">
            <span className="w-2 h-2 bg-[var(--secondary)] rounded-full animate-pulse" />
            Stock permanente garantizado
          </div>

          {/* Headline */}
          <h1 className="font-[var(--font-epilogue)] text-4xl md:text-6xl font-bold text-white leading-tight">
            Materiales eléctricos en{" "}
            <span className="text-[#ffb4ac]">La Falda</span>
          </h1>

          {/* Subheadline */}
          <p className="text-lg text-white/80 max-w-xl mx-auto font-[var(--font-hanken)]">
            Stock disponible para electricistas, instaladores y constructoras.
            Atención mayorista y minorista.
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap justify-center gap-4 pt-4">
            <a
              href={`https://wa.me/${WA_NUMBER}?text=${WA_MESSAGE}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="whatsapp" size="lg">
                Consultar por WhatsApp
              </Button>
            </a>
            <a href="tel:+5493548575510">
              <Button variant="secondary" size="lg" className="border-2 border-white text-white hover:bg-white/10">
                Llamanos
              </Button>
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-12 border-t border-white/10">
            {STATS.map((stat) => (
              <div key={stat.label} className="space-y-1">
                <p className="text-2xl font-bold text-white font-[var(--font-epilogue)]">
                  {stat.value}
                </p>
                <p className="text-white/60 text-sm font-[var(--font-hanken)]">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}