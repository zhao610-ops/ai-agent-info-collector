import Link from "next/link";

const links = [["/", "Dashboard"], ["/reports", "周报"], ["/agents", "Agents"], ["/github", "GitHub"], ["/settings", "设置"]];

export function Nav() {
  return <header className="border-b bg-white"><div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4"><Link href="/" className="font-bold">AI Agent Weekly Radar</Link><nav className="flex flex-wrap gap-5 text-sm">{links.map(([href, label]) => <Link key={href} href={href} className="text-slate-600 hover:text-blue-600">{label}</Link>)}</nav></div></header>;
}
