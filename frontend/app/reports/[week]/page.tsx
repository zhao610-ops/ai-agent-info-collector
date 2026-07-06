"use client";

import { use, useEffect, useState } from "react";
import { api, API_BASE } from "@/lib/api";
import { Notice } from "@/components/Notice";
import { StatusBadge } from "@/components/StatusBadge";

type Report = { week:string; title:string; content_html:string; content_md:string; generation_mode:string; llm_provider:string; llm_model:string; push_status:string; created_at:string; wordcloud_image:string; github_chart_image:string; keyword_trend_image:string };
const charts = [
  ["wordcloud.png", "本周热词云", "wordcloud_image"],
  ["github_growth_top10.png", "GitHub Star 增长 TOP10", "github_chart_image"],
  ["keyword_trend.png", "关键词近 4～8 周趋势", "keyword_trend_image"],
] as const;

export default function ReportDetail({ params }: { params:Promise<{week:string}> }) {
  const { week } = use(params);
  const [row, setRow] = useState<Report|null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Report>(`/api/reports/${week}`).then(setRow).catch(error => setError(error.message)).finally(() => setLoading(false));
  }, [week]);

  if (loading) return <div className="empty">正在加载周报…</div>;
  if (error || !row) return <Notice message={error || "周报不存在"} error />;
  return <div className="space-y-6">
    <div><div className="flex flex-wrap items-center gap-2"><h1 className="text-2xl font-bold">{row.title}</h1><StatusBadge status={row.generation_mode}/><StatusBadge status={row.push_status}/></div><p className="mt-2 text-sm text-slate-500">生成时间：{new Date(row.created_at).toLocaleString()} · 模型：{row.generation_mode === "llm" ? `${row.llm_provider} / ${row.llm_model}` : "Template"}</p></div>
    <div className="grid gap-4 lg:grid-cols-3">{charts.map(([name, title, field]) => <figure className="card p-3" key={name}>{row[field]?<img className="h-auto w-full" src={`${API_BASE}/api/reports/${week}/images/${name}`} alt={title}/>:<div className="empty py-16">该图表生成失败，请查看 Agent 日志。</div>}<figcaption className="mt-2 text-center text-sm text-slate-600">{title}</figcaption></figure>)}</div>
    <article className="card prose max-w-none" dangerouslySetInnerHTML={{ __html: row.content_html }}/>
  </div>;
}
