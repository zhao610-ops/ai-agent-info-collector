"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Notice } from "@/components/Notice";

type Repo = { full_name:string; url:string; description:string; language:string; stars:number; forks:number; pushed_at:string|null; stars_growth_7d:number; topics:string[]; heat_score:number; agent_relevance_score:number };

export default function Github() {
  const [rows, setRows] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => { api<Repo[]>("/api/github/hot").then(setRows).catch(error => setError(error.message)).finally(() => setLoading(false)); }, []);

  return <div className="space-y-6"><div><h1 className="text-2xl font-bold">GitHub 热门项目</h1><p className="text-sm text-slate-500">结合增长、热度和 Agent 相关度分析项目。</p></div><Notice message={error} error />
    {loading ? <div className="empty">正在加载项目…</div> : rows.length ? <div className="card overflow-x-auto"><table className="w-full min-w-[1100px] text-left text-sm"><thead><tr className="border-b text-slate-500"><th className="p-2">项目</th><th>语言</th><th>Stars</th><th>Forks</th><th>7 日增长</th><th>热度</th><th>相关度</th><th>最近推送</th><th>Topics</th></tr></thead><tbody>{rows.map(row => <tr key={row.full_name} className="border-b align-top last:border-0"><td className="p-2"><a className="font-medium text-blue-700" target="_blank" rel="noreferrer" href={row.url}>{row.full_name}</a><p className="mt-1 max-w-sm text-xs text-slate-500">{row.description || "暂无描述"}</p></td><td>{row.language || "-"}</td><td>{row.stars.toLocaleString()}</td><td>{row.forks.toLocaleString()}</td><td className="font-medium text-emerald-600">+{row.stars_growth_7d}</td><td>{row.heat_score}</td><td>{row.agent_relevance_score}</td><td className="text-xs">{row.pushed_at ? new Date(row.pushed_at).toLocaleDateString() : "-"}</td><td><div className="flex max-w-xs flex-wrap gap-1">{row.topics.map(topic => <span className="rounded bg-slate-100 px-2 py-1 text-xs" key={topic}>{topic}</span>)}</div></td></tr>)}</tbody></table></div> : <div className="empty">暂无 GitHub 项目数据。</div>}
  </div>;
}
