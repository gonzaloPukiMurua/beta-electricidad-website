// Nunca "sin stock": si no hay, se invita a consultar (D-008 / REQ-029).
export function Disponibilidad({ disponible }: { disponible: boolean }) {
  return disponible ? (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700">
      <span className="h-2 w-2 rounded-full bg-emerald-600" aria-hidden="true" />
      Disponible
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-700">
      <span className="h-2 w-2 rounded-full bg-amber-500" aria-hidden="true" />
      Consultá disponibilidad
    </span>
  );
}
