import { redirect } from "next/navigation";

import { defaultLocale } from "@/lib/i18n/config";

/** Fallback when middleware does not run for `/` (avoids blank root). */
export default function RootPage() {
  redirect(`/${defaultLocale}`);
}
