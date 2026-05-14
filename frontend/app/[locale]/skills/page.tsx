import { getDictionary } from "@/lib/i18n/get-dictionary";
import { SkillsLibrary, type SkillsLabels } from "@/components/SkillsLibrary";

export default async function SkillsPage({ params }: { params: { locale: string } }) {
  const dict = await getDictionary(params.locale);
  const app = dict.app as Record<string, unknown>;
  return <SkillsLibrary labels={app.skillsPage as SkillsLabels} />;
}
