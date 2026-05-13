import type { Locale } from "./config";

const loaders: Record<Locale, () => Promise<Record<string, unknown>>> = {
  en: () => import("@/messages/en.json").then((m) => m.default as Record<string, unknown>),
  zh: () => import("@/messages/zh.json").then((m) => m.default as Record<string, unknown>),
};

export async function getDictionary(locale: string) {
  const loc = locale === "zh" ? "zh" : "en";
  return loaders[loc]();
}
