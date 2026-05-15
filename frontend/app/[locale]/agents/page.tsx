import { getDictionary } from "@/lib/i18n/get-dictionary";
import { AgentsConsole, type AgentsConsoleLabels } from "@/components/AgentsConsole";

export default async function AgentsPage({ params }: { params: { locale: string } }) {
  const dict = await getDictionary(params.locale);
  const app = dict.app as Record<string, unknown>;
  return <AgentsConsole labels={app.agentsPage as AgentsConsoleLabels} />;
}
