import { getDictionary } from "@/lib/i18n/get-dictionary";

export default async function AgentsPage({ params }: { params: { locale: string } }) {
  const d = await getDictionary(params.locale);
  const wip = (d.common as { wip: string }).wip;
  return <p className="text-sm text-zinc-400">{wip}</p>;
}
