"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Notice } from "@/components/Notice";
import { StatusBadge } from "@/components/StatusBadge";

type Report = { week:string; title:string; summary:string; created_at:string; generation_mode:string; llm_provider:string; llm_model:string; push_status:string };

export default function Reports() {
  const [rows, setRows] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Report[]>("/api/reports").then(setRows).catch(error => setError(error.message)).finally(() => setLoading(false));
  }, []);

  return <div className="space-y-6">
    <div><h1 className="text-2xl font-bold">历史周报</h1><p className="text-sm text-slate-500">查看每周生成方式、模型和推送状态。</p></div>
    <Notice message={error} error />
    {loading ? <div className="empty">正在加载周报…</div> : rows.length ? <div className="space-y-4">{rows.map(row =>
      <Link href={`/reports/${row.week}`} key={row.week} className="card block hover:border-blue-300">
        <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="font-semibold">{row.title}</h2><p className="mt-1 text-xs text-slate-500">{new Date(row.created_at).toLocaleString()}</p></div><div className="flex gap-2"><StatusBadge status={row.generation_mode}/><StatusBadge status={row.push_status}/></div></div>
        <p className="mt-3 line-clamp-2 text-sm text-slate-600">{row.summary}</p>
        <p className="mt-3 text-xs text-slate-500">模型：{row.generation_mode === "llm" ? `${row.llm_provider} / ${row.llm_model}` : "模板降级"}</p>
      </Link>)}</div> : <div className="empty">暂无周报，请先在 Dashboard 手动运行。</div>}
  </div>;
}
