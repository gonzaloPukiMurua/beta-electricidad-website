"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { IndicadorLista } from "@/components/presupuesto/BotonAgregar";

// Rutas absolutas ("/#...") para que funcionen también desde /catalogo y /producto.
const NAV_LINKS = [
  { label: "Inicio", href: "/" },
  { label: "Catálogo", href: "/catalogo" },
  { label: "Rubros", href: "/#rubros" },
  { label: "Nosotros", href: "/#nosotros" },
  { label: "Contacto", href: "/#contacto" },
];
// "Solicitar Presupuesto" lleva a la lista; la consulta directa sigue en el botón flotante de WhatsApp.
const PRESUPUESTO_HREF = "/presupuesto";

function activo(href: string, pathname: string) {
  if (href === "/") return pathname === "/";
  if (href === "/catalogo") return pathname.startsWith("/catalogo") || pathname.startsWith("/producto");
  return false;
}

export function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();

  return (
    <header className="fixed top-0 left-0 w-full z-50 h-20 px-4 md:px-10 bg-[var(--surface)]/80 backdrop-blur-md border-b border-[var(--outline-variant)]/30 flex items-center justify-center">
      <div className="max-w-[1280px] w-full flex justify-between items-center">

        {/* Logo */}
        <Link href="/" className="flex items-center">
          <span className="text-xl font-bold text-[var(--primary)] font-[var(--font-epilogue)]">
            Beta Electricidad
          </span>
        </Link>

        {/* Nav desktop */}
        <nav className="hidden md:flex gap-8 items-center">
          {NAV_LINKS.map((link) => (
           <Link
              key={link.href}
              href={link.href}
              className={
                activo(link.href, pathname)
                  ? "text-[var(--primary)] font-semibold border-b-2 border-[var(--primary)] pb-1 text-sm"
                  : "text-[var(--on-surface-variant)] hover:text-[var(--primary)] transition-colors text-sm"
              }
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* CTA + hamburger */}
        <div className="flex items-center gap-3 md:gap-4">
          <IndicadorLista onClick={() => setMenuOpen(false)} />
          <Link href={PRESUPUESTO_HREF} className="hidden lg:block bg-[var(--primary)] text-[var(--on-primary)] px-6 py-2.5 rounded-lg text-xs font-semibold tracking-wide hover:opacity-90 active:scale-95 transition-all shadow-sm">
            Solicitar Presupuesto
          </Link>
          <button
            className="md:hidden text-[var(--primary)]"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Abrir menú"
          >
            <span className="text-3xl">{menuOpen ? "✕" : "☰"}</span>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="absolute top-20 left-0 w-full bg-[var(--surface)] border-b border-[var(--outline-variant)]/30 flex flex-col px-4 py-4 gap-4 md:hidden">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-[var(--on-surface)] text-sm font-medium hover:text-[var(--primary)] transition-colors"
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <Link href={PRESUPUESTO_HREF} onClick={() => setMenuOpen(false)} className="bg-[var(--primary)] text-[var(--on-primary)] px-6 py-2.5 rounded-lg text-xs font-semibold tracking-wide w-full text-center">
            Solicitar Presupuesto
          </Link>
        </div>
      )}
    </header>
  );
}