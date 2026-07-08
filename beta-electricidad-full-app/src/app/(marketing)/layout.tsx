import { Navbar } from "@/components/marketing/Navbar";
import { WhatsAppCTA } from "@/components/marketing/WhatsAppCTA";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <Navbar/>
      <WhatsAppCTA />
    </>
  );
}