import { getDictionary } from "@/lib/i18n/get-dictionary";

type HomeDict = {
  name: string;
  tagline: string;
  home: {
    phaseLabel: string;
    phaseBody: string;
    apiStatus: string;
    notSet: string;
    openDashboard: string;
    apiSameOrigin: string;
    apiExplicit: string;
  };
};

export default async function HomePage({ params }: { params: { locale: string } }) {
  const dict = await getDictionary(params.locale);
  const app = dict.app as HomeDict;
  const apiExplicit = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">{app.name}</h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-400 sm:text-base">{app.tagline}</p>
      </div>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 sm:p-6">
        <p className="text-xs font-medium uppercase tracking-wide text-amber-400">{app.home.phaseLabel}</p>
        <p className="mt-2 text-sm leading-relaxed text-zinc-300">{app.home.phaseBody}</p>
        <dl className="mt-6 grid gap-2 text-sm text-zinc-400">
          <div className="flex flex-wrap gap-2">
            <dt className="text-zinc-500">{app.home.apiStatus}</dt>
            <dd className="max-w-xl text-zinc-200">
              {apiExplicit ? (
                <>
                  <span className="text-zinc-500">{app.home.apiExplicit}: </span>
                  <span className="font-mono text-sm">{apiExplicit}</span>
                </>
              ) : (
                <span>{app.home.apiSameOrigin}</span>
              )}
            </dd>
          </div>
        </dl>
        <p className="mt-4 text-sm">
          <a className="text-sky-400 hover:underline" href={`/${params.locale}/dashboard`}>
            → {app.home.openDashboard}
          </a>
        </p>
      </div>
    </div>
  );
}
