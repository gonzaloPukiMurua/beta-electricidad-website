const PILARES = [
  {
    titulo: "Stock disponible",
    descripcion: "Materiales listos para retirar o enviar.",
    icono: "📦",
  },
  {
    titulo: "Precios competitivos",
    descripcion: "Listas de precio para electricistas y mayoristas.",
    icono: "💰",
  },
  {
    titulo: "En La Falda",
    descripcion: "Atención local con asesoramiento técnico.",
    icono: "📍",
  },
];

export function ValorSection() {
  return (
    <section id="nosotros" className="scroll-mt-20 py-20 px-6 bg-white">
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-10 text-center">
        {PILARES.map((p) => (
          <div key={p.titulo}>
            <span className="text-4xl">{p.icono}</span>
            <h3 className="text-xl font-bold mt-4 mb-2 text-[var(--brand-secondary)]">{p.titulo}</h3>
            <p className="text-[var(--text-muted)]">{p.descripcion}</p>
          </div>
        ))}
      </div>
    </section>
  );
}