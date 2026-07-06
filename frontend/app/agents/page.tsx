"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Notice } from "@/components/Notice";
import { StatusBadge } from "@/components/StatusBadge";

type Run = { id:number; run_id:string; week:string; agent_name:string; status:string; error:string; output_count:number; duration_ms:number; started_at:string; finished_at:string|null };
const pipeline = ["OrchestratorAgent", "NewsAgent", "GitHubAgent", "TrendAgent", "VisualizationAgent", "ReportAgent", "ServerChanPushAgent"];

export default function Agents() {
  const [rows, setRows] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => { api<Run[]>("/api/agents/runs").then(setRows).catch(error => setError(error.message)).finally(() => setLoading(false)); }, []);
  const latestRunId = rows[0]?.run_id;
  const latest = useMemo(() => pipeline.map(name => rows.find(row => row.run_id === latestRunId && row.agent_name === name)).filter(Boolean) as Run[], [rows, latestRunId]);

  return <div className="space-y-6">
    <div><h1 className="text-2xl font-bold">多 Agent 执行链路</h1><p className="text-sm text-slate-500">最近运行的编排、耗时、输出数量和降级信息。</p></div>
    <Notice message={error} error />
    {loading ? <div className="empty">正在加载 Agent 状态…</div> : latest.length ? <div className="grid gap-3 lg:grid-cols-7">{latest.map((run, index) => <div className="card relative p-4" key={run.id}><div className="mb-3 flex items-center justify-between"><span className="text-xs text-slate-400">{index + 1}</span><StatusBadge status={run.status}/></div><h2 className="break-words text-sm font-semibold">{run.agent_name}</h2><div className="mt-3 space-y-1 text-xs text-slate-500"><p>输出：{run.output_count}</p><p>耗时：{run.duration_ms.toLocaleString()} ms</p></div>{run.error && <p className="mt-3 break-words text-xs text-amber-700">{run.error}</p>}</div>)}</div> : <div className="empty">暂无运行记录。</div>}
    {!loading && rows.length > 0 && <section className="card overflow-x-auto"><h2 className="mb-4 font-semibold">最近运行记录</h2><table className="w-full min-w-[900px] text-left text-sm"><thead><tr className="border-b text-slate-500"><th className="p-2">周次</th><th>Agent</th><th>状态</th><th>输出</th><th>耗时</th><th>开始时间</th><th>结束时间</th><th>错误/降级</th></tr></thead><tbody>{rows.map(run => <tr key={run.id} className="border-b last:border-0"><td className="p-2">{run.week}</td><td>{run.agent_name}</td><td><StatusBadge status={run.status}/></td><td>{run.output_count}</td><td>{run.duration_ms} ms</td><td>{new Date(run.started_at).toLocaleString()}</td><td>{run.finished_at ? new Date(run.finished_at).toLocaleString() : "-"}</td><td className="max-w-xs whitespace-normal text-xs text-amber-700">{run.error || "-"}</td></tr>)}</tbody></table></section>}
  </div>;
}
