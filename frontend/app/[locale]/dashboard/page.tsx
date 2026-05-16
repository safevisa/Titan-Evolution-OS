import { getDictionary } from "@/lib/i18n/get-dictionary";
import { DashboardConsole, type DashboardLabels } from "@/components/DashboardConsole";

export default async function DashboardPage({ params }: { params: { locale: string } }) {
  const dict = await getDictionary(params.locale);
  const app = dict.app as Record<string, unknown>;
  return <DashboardConsole labels={app.dashboard as DashboardLabels} />;
}
