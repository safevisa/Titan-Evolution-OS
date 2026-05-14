import { getDictionary } from "@/lib/i18n/get-dictionary";
import { SettingsConsole, type SettingsLabels } from "@/components/SettingsConsole";

export default async function SettingsPage({ params }: { params: { locale: string } }) {
  const dict = await getDictionary(params.locale);
  const app = dict.app as Record<string, unknown>;
  return <SettingsConsole labels={app.settingsPage as SettingsLabels} />;
}
