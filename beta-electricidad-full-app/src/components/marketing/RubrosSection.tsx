const RUBROS = [
  "Iluminación",
  "Canalizaciones",
  "Tableros y envolventes",
  "Elementos de protección",
  "Comando y Automatización",
  "Instrumental",
  "Llaves",
];

export function RubrosSection() {
  return (
    <section className="py-20 px-6 bg-gray-50">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold text-center text-[var(--brand-secondary)] mb-12">
          Nuestros rubros
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {RUBROS.map((rubro) => (
            <div
              key={rubro}
              className="rounded-xl border border-gray-200 bg-white px-4 py-6 text-center text-sm font-medium text-[var(--brand-secondary)] hover:border-[var(--brand-primary)] hover:shadow-sm transition-all"
            >
              {rubro}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}