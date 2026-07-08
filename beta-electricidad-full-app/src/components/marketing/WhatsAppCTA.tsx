"use client";

import { WA_NUMBER, WA_MESSAGE } from "@/lib/constants/whatsApp";

export function WhatsAppCTA() {
  return (
    <a 
      href={`https://wa.me/${WA_NUMBER}?text=${WA_MESSAGE}`}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Consultar por WhatsApp"
      className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-[var(--brand-accent)] px-4 py-3 text-white shadow-lg hover:brightness-110 transition-all"
    >
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
        <path d="M12 0C5.373 0 0 5.373 0 12c0 2.123.554 4.17 1.535 5.943L.057 23.75a.75.75 0 00.918.943l5.98-1.42A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.75a9.73 9.73 0 01-4.964-1.355l-.355-.213-3.683.875.936-3.558-.233-.368A9.75 9.75 0 1112 21.75z"/>
      </svg>
      <span className="text-sm font-semibold">Consultar</span>
    </a>
  );
}