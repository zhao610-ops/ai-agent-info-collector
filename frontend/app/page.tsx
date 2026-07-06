"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Notice } from "@/components/Notice";
import { StatusBadge } from "@/components/StatusBadge";

type Report = { week:string; title:string; summary:string; generation_mode:string; pushed_at:string|null; push_status:string };
type Trend = { keyword:string; frequency:number; trend_score:number };
type Repo = { full_name:string; stars:number; stars_growth_7d:number; url:string };
type Run = { id:number; run_id:string; week:string; agent_name:string; status:string; duration_ms:number; started_at:string };

export default function Dashboard() {
  const [report, setReport] = useState<Report|null>(null); const [reports, setReports] = useState<Report[]>([]); const [selectedWeek, setSelectedWeek] = useState("");
  const [trends, setTrends] = useState<Trend[]>([]); const [repos, setRepos] = useState<Repo[]>([]); const [latestRun, setLatestRun] = useState<Run|null>(null);
  const [message, setMessage] = useState(""); const [isError, setIsError] = useState(false); const [loading, setLoading] = useState(true); const [running, setRunning] = useState(false); const [pushing, setPushing] = useState(false);

  async function load() {
    // 各区域独立依赖同一周次，后端默认返回最近生成的周报数据。
    const [reportRows, trendRows, repoRows, runs] = await Promise.all([api<Report[]>("/api/reports"), api<Trend[]>("/api/keywords/trends"), api<Repo[]>("/api/github/hot"), api<Run[]>("/api/agents/runs?limit=50")]);
    setReports(reportRows); setReport(reportRows[0] || null); setSelectedWeek(current => current || reportRows[0]?.week || ""); setTrends(trendRows); setRepos(repoRows);
    setLatestRun(runs.find(run => run.agent_name === "OrchestratorAgent") || null);
  }
  useEffect(() => { load().catch(error => {setMessage(error.message);setIsError(true);}).finally(() => setLoading(false)); }, []);

  async function run() {
    setRunning(true);setMessage("");setIsError(false);
    try { await api("/api/agents/run-weekly", {method:"POST"}); setMessage("周报任务已提交，可在 Agents 页面查看实时执行链路。"); setTimeout(() => load().catch(() => undefined), 2000); }
    catch (error) { setMessage(error instanceof Error ? error.message : "任务提交失败");setIsError(true); }
    finally { setRunning(false); }
  }
  async function pushReport() {
    const selected = reports.find(item => item.week === selectedWeek);
    if (selected?.pushed_at) { window.alert("该周报已经推送过，不能重复推送"); return; }
    if (!window.confirm(`确认将 ${selectedWeek} 周报推送到微信？`)) return;
    setPushing(true);
    try { const result = await api<{message:string}>(`/api/reports/${selectedWeek}/push`, {method:"POST"}); window.alert(result.message); await load(); }
    catch (error) { window.alert(error instanceof Error ? error.message : "微信推送失败"); }
    finally { setPushing(false); }
  }

  return <div className="space-y-6"><div className="flex flex-wrap items-center justify-between gap-4"><div><h1 className="text-2xl font-bold">AI Agent Weekly Radar</h1><p className="text-slate-500">多 Agent 协作的 AI 行业情报周报系统</p></div><div className="flex flex-wrap items-center gap-2"><button className="btn" disabled={running} onClick={run}>{running?"提交中…":"手动运行周报"}</button><select className="input w-auto min-w-36" value={selectedWeek} onChange={event=>setSelectedWeek(event.target.value)} disabled={!reports.length||pushing} aria-label="选择要推送的周报"><option value="" disabled>选择周报</option>{reports.map(item=><option key={item.week} value={item.week}>{item.week}{item.pushed_at?"（已推送）":""}</option>)}</select><button className="btn bg-slate-700 hover:bg-slate-800" onClick={pushReport} disabled={!selectedWeek||pushing}>{pushing?"推送中…":"确认推送微信"}</button></div></div><Notice message={message} error={isError}/>
    {loading ? <div className="empty">正在加载 Dashboard…</div> : <><div className="grid gap-4 md:grid-cols-3"><div className="metric"><p className="text-xs text-slate-500">最新周报</p><p className="mt-1 font-semibold">{report?.week || "暂无"}</p></div><div className="metric"><p className="text-xs text-slate-500">生成方式</p><div className="mt-1">{report?<StatusBadge status={report.generation_mode}/>:"-"}</div></div><div className="metric"><p className="text-xs text-slate-500">最近运行</p><div className="mt-1 flex items-center gap-2">{latestRun?<><StatusBadge status={latestRun.status}/><span className="text-xs text-slate-500">{latestRun.duration_ms} ms</span></>:"暂无"}</div></div></div>
    <section className="card"><div className="mb-2 flex justify-between"><h2 className="font-semibold">本周核心结论</h2>{report&&<StatusBadge status={report.push_status}/>}</div><p className="text-slate-700">{report?.summary||"暂无周报，请先运行任务。"}</p>{report&&<Link className="mt-3 inline-block text-sm text-blue-600" href={`/reports/${report.week}`}>查看完整周报 →</Link>}</section>
    <div className="grid gap-6 lg:grid-cols-2"><section className="card"><h2 className="mb-4 font-semibold">本周热词 TOP10</h2>{trends.length?<div className="flex flex-wrap gap-2">{trends.slice(0,10).map(item=><span key={item.keyword} className="rounded-full bg-blue-50 px-3 py-1 text-sm text-blue-700">{item.keyword} · {item.frequency}</span>)}</div>:<p className="text-sm text-slate-500">暂无趋势数据。</p>}</section><section className="card"><h2 className="mb-4 font-semibold">GitHub 增长 TOP10</h2>{repos.length?<ol className="space-y-2">{repos.slice(0,10).map((item,index)=><li key={item.full_name} className="flex justify-between gap-3 text-sm"><a href={item.url} target="_blank" rel="noreferrer" className="text-blue-700">{index+1}. {item.full_name}</a><span className="text-emerald-600">+{item.stars_growth_7d}</span></li>)}</ol>:<p className="text-sm text-slate-500">暂无 GitHub 数据。</p>}</section></div></>}
  </div>;
}
