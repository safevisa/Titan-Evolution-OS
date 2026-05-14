import { getDictionary } from "@/lib/i18n/get-dictionary";
import { BillingConsole, type BillingLabels } from "@/components/BillingConsole";

export default async function BillingPage({ params }: { params: { locale: string } }) {
  const dict = await getDictionary(params.locale);
  const app = dict.app as Record<string, unknown>;
  return <BillingConsole labels={app.billingPage as BillingLabels} />;
}
