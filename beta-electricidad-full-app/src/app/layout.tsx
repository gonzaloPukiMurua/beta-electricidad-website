import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Epilogue, Hanken_Grotesk } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://betaelectricidad.com.ar";

const epilogue = Epilogue({
  variable: "--font-epilogue",
  subsets: ["latin"],
  weight: ["400", "600", "700", "800"],
});

const hanken = Hanken_Grotesk({
  variable: "--font-hanken",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  // Fuera de producción (NEXT_PUBLIC_INDEXAR != "true") no se indexa. Ver robots.ts.
  robots: process.env.NEXT_PUBLIC_INDEXAR === "true" ? undefined : { index: false, follow: false },
  title: {
    default: "Beta Electricidad | Materiales Eléctricos en La Falda, Córdoba",
    template: "%s | Beta Electricidad",
  },
  description: "Venta de materiales eléctricos, iluminación e instrumental en La Falda, Córdoba. Atención a electricistas, constructoras e instaladores.",
  keywords: ["materiales eléctricos", "electricidad La Falda", "iluminación Córdoba", "instrumental eléctrico"],
  openGraph: {
    type: "website",
    locale: "es_AR",
    url: SITE_URL,
    siteName: "Beta Electricidad",
  },
};

const localBusinessSchema = {
  "@context": "https://schema.org",
  "@type": "ElectricalSupply",
  name: "Beta Electricidad",
  description: "Venta de materiales eléctricos, iluminación e instrumental",
  url: SITE_URL,
  telephone: ["+5493548575510"],
  address: {
    "@type": "PostalAddress",
    streetAddress: "9 de Julio 433",
    addressLocality: "La Falda",
    postalCode: "5172",
    addressRegion: "Córdoba",
    addressCountry: "AR",
  },
  geo: {
    "@type": "GeoCoordinates",
    latitude: -31.0875,
    longitude: -64.4956,
  },
  openingHoursSpecification: [
    {
      "@type": "OpeningHoursSpecification",
      dayOfWeek: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      opens: "09:00",
      closes: "17:00",
    },
    {
      "@type": "OpeningHoursSpecification",
      dayOfWeek: "Saturday",
      opens: "09:00",
      closes: "13:00",
    },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es-AR">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(localBusinessSchema) }}
        />
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable} ${epilogue.variable} ${hanken.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}