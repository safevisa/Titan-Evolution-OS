import { getDictionary } from "@/lib/i18n/get-dictionary";
import { EvolutionConsole, type EvolutionLabels } from "@/components/EvolutionConsole";

export default async function EvolutionPage({ params }: { params: { locale: string } }) {
  const dict = await getDictionary(params.locale);
  const app = dict.app as Record<string, unknown>;
  return <EvolutionConsole labels={app.evolutionPage as EvolutionLabels} />;
}
