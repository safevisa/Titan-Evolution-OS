import { notFound } from "next/navigation";
import { isLocale, locales } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { AppSidebar, type SidebarLabels } from "@/components/AppSidebar";

type AppDict = {
  name: string;
  tagline: string;
  nav: SidebarLabels;
};

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  if (!isLocale(params.locale)) {
    notFound();
  }
  const dict = await getDictionary(params.locale);
  const app = dict.app as AppDict;

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#07090f", fontFamily: "'DM Sans','Helvetica Neue',sans-serif" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap'); * { box-sizing: border-box; } ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-track { background: transparent; } ::-webkit-scrollbar-thumb { background: #2a2e3a; border-radius: 2px; }`}</style>
      <AppSidebar locale={params.locale} labels={app.nav} />
      <main style={{ flex: 1, padding: "32px 36px", overflowY: "auto", minWidth: 0 }}>
        {children}
      </main>
    </div>
  );
}
