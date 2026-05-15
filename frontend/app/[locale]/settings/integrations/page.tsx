import { getDictionary } from "@/lib/i18n/get-dictionary";
import {
  IntegrationsConsole,
  type IntegrationsLabels,
} from "@/components/IntegrationsConsole";

export default async function IntegrationsSettingsPage({
  params,
}: {
  params: { locale: string };
}) {
  const dict = await getDictionary(params.locale);
  const app = dict.app as Record<string, unknown>;
  return (
    <IntegrationsConsole
      locale={params.locale}
      labels={app.integrationsPage as IntegrationsLabels}
    />
  );
}
