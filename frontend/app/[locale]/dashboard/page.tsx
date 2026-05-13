import { getDictionary } from "@/lib/i18n/get-dictionary";
import { QuickStartConsole, type QuickStartLabels } from "@/components/QuickStartConsole";

export default async function DashboardPage({ params }: { params: { locale: string } }) {
  const dict = await getDictionary(params.locale);
  const app = dict.app as Record<string, unknown>;
  const qs = app.quickstart as QuickStartLabels;

  return (
    <div className="space-y-8">
      <QuickStartConsole labels={qs} locale={params.locale} />
    </div>
  );
}
