import { notFound } from "next/navigation";

import { AppNav, type NavLabels } from "@/components/AppNav";
import { isLocale, locales } from "@/lib/i18n/config";
import { getDictionary } from "@/lib/i18n/get-dictionary";
import { Providers } from "../providers";

type AppDict = {
  name: string;
  tagline: string;
  nav: NavLabels;
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
    <Providers>
      <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
        <AppNav locale={params.locale} title={app.name} nav={app.nav} />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">{children}</main>
      </div>
    </Providers>
  );
}
