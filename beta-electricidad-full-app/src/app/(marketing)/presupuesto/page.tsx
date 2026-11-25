import type { Metadata } from "next";
import { ListaPresupuesto } from "@/components/presupuesto/ListaPresupuesto";

export const metadata: Metadata = {
  title: "Mi lista para presupuestar",
  description: "Armá tu lista de materiales eléctricos y pedí la cotización por WhatsApp o email a Beta Electricidad, La Falda.",
  robots: { index: false, follow: true }, // es personal de cada visitante
};

export default function PresupuestoPage() {
  return (
    <main className="mx-auto max-w-[900px] px-4 pb-28 pt-28 md:px-10">
      <h1 className="text-3xl font-bold text-[var(--primary)]">Mi lista para presupuestar</h1>
      <p className="mt-1 text-sm text-[var(--on-surface-variant)]">
        Agregá productos desde el catálogo, ajustá las cantidades y mandanos la lista. Te respondemos con el presupuesto y el precio del día.
      </p>
      <ListaPresupuesto />
    </main>
  );
}
