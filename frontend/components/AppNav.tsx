import Link from "next/link";

export type NavLabels = {
  dashboard: string;
  agents: string;
  tasks: string;
  evolution: string;
  skills: string;
  settings: string;
};

export function AppNav({
  locale,
  title,
  nav,
}: {
  locale: string;
  title: string;
  nav: NavLabels;
}) {
  const p = `/${locale}`;
  const links: { href: string; label: string }[] = [
    { href: `${p}/dashboard`, label: nav.dashboard },
    { href: `${p}/agents`, label: nav.agents },
    { href: `${p}/tasks`, label: nav.tasks },
    { href: `${p}/evolution`, label: nav.evolution },
    { href: `${p}/skills`, label: nav.skills },
    { href: `${p}/settings`, label: nav.settings },
  ];
  return (
    <header className="border-b border-zinc-800 bg-zinc-900/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href={`${p}/dashboard`} className="text-sm font-semibold tracking-tight text-white">
          {title}
        </Link>
        <nav className="flex flex-wrap items-center gap-3 text-xs text-zinc-400 sm:text-sm">
          {links.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-2 py-1 transition hover:bg-zinc-800 hover:text-zinc-100"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
