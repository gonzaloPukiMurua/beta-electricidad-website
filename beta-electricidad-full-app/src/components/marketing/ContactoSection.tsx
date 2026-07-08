export function ContactoSection() {
  return (
    <section className="py-20 px-6 bg-white">
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
        
        {/* Datos de contacto */}
        <div>
          <h2 className="text-3xl font-bold text-[var(--brand-secondary)] mb-8">
            Contacto
          </h2>
          <ul className="space-y-4 text-[var(--text-base)]">
            <li>
              <span className="font-semibold">Dirección:</span>{" "}
              9 de Julio 433, La Falda, Córdoba (CP 5172)
            </li>
            <li>
              <span className="font-semibold">Teléfono:</span>{" "}
              <a href="tel:+5493548575510" className="hover:text-[var(--brand-primary)] transition-colors">
                +54 9 3548 575510
              </a>
            </li>
            <li>
              <span className="font-semibold">Horario:</span>{" "}
              Lun–Vie 9:00 a 17:00 · Sáb 9:00 a 13:00
            </li>
          </ul>
        </div>

        {/* Google Maps embed */}
        <div className="rounded-xl overflow-hidden border border-gray-200 h-64 md:h-80">
          <iframe
            src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3396.1!2d-64.4956!3d-31.0875!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2z9iBkZSBKdWxpbyA0MzM!5e0!3m2!1ses!2sar!4v1"
            width="100%"
            height="100%"
            style={{ border: 0 }}
            allowFullScreen
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
            title="Ubicación Beta Electricidad"
          />
        </div>

      </div>
    </section>
  );
}