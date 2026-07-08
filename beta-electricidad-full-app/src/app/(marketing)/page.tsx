import { HeroSection } from "@/components/marketing/HeroSection";
import { ValorSection } from "@/components/marketing/ValorSection";
import { RubrosSection } from "@/components/marketing/RubrosSection";
import { ContactoSection } from "@/components/marketing/ContactoSection";

export default function HomePage() {
  return (
    <main>
      <HeroSection />
      <ValorSection />
      <RubrosSection />
      <ContactoSection />
    </main>
  );
}