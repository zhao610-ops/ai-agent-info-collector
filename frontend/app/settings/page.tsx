"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Notice } from "@/components/Notice";
import { StatusBadge } from "@/components/StatusBadge";

type LLMConfig = { enabled:boolean; provider:string; base_url:string; model:string; api_key_configured:boolean; api_key?:string };
type PushItem = { id:number; week:string; status:string; error_message:string; created_at:string };
type ServerConfig = { enabled:boolean; sendkey_configured:boolean; api_base:string; sendkey?:string; recent_pushes:PushItem[] };
const providers = [
  {value:"deepseek",label:"DeepSeek",base_url:"https://api.deepseek.com",model:"deepseek-chat"},
  {value:"qwen",label:"Qwen / 通义千问",base_url:"https://dashscope.aliyuncs.com/compatible-mode/v1",model:"qwen-plus"},
  {value:"kimi",label:"Kimi / Moonshot",base_url:"https://api.moonshot.ai/v1",model:"kimi-latest"},
  {value:"siliconflow",label:"SiliconFlow",base_url:"https://api.siliconflow.cn/v1",model:"deepseek-ai/DeepSeek-V3"},
  {value:"custom",label:"Custom OpenAI Compatible",base_url:"",model:""},
];

export default function Settings() {
  const [form, setForm] = useState<LLMConfig>({enabled:false,provider:"deepseek",base_url:"",model:"",api_key_configured:false,api_key:""});
  const [server, setServer] = useState<ServerConfig>({enabled:false,sendkey_configured:false,api_base:"https://sctapi.ftqq.com",sendkey:"",recent_pushes:[]});
  const [message, setMessage] = useState(""); const [isError, setIsError] = useState(false); const [busy, setBusy] = useState(""); const [loading, setLoading] = useState(true);

  async function load() {
    const [llm, push] = await Promise.all([api<LLMConfig>("/api/settings/llm"), api<ServerConfig>("/api/settings/serverchan")]);
    setForm({...llm, api_key:""}); setServer({...push, sendkey:""});
  }
  useEffect(() => { load().catch(error => {setMessage(error.message);setIsError(true);}).finally(() => setLoading(false)); }, []);
  function providerChanged(value:string) { const item = providers.find(provider => provider.value === value)!; setForm({...form,provider:value,base_url:item.base_url,model:item.model}); }
  async function action(name:string, task:()=>Promise<string>) { setBusy(name);setMessage("");setIsError(false);try{setMessage(await task());}catch(error){setMessage(error instanceof Error?error.message:"操作失败");setIsError(true);}finally{setBusy("");} }

  if (loading) return <div className="empty">正在加载配置…</div>;
  return <div className="space-y-6"><div><h1 className="text-2xl font-bold">系统设置</h1><p className="text-sm text-slate-500">密钥不会返回前端，留空保存会保留原值。</p></div><Notice message={message} error={isError}/>
    <section className="card space-y-4"><div><h2 className="font-semibold">大模型配置</h2><p className="text-sm text-slate-500">调用失败时自动降级为模板周报。</p></div><label className="flex items-center gap-3"><input type="checkbox" checked={form.enabled} onChange={event=>setForm({...form,enabled:event.target.checked})}/><span className="text-sm">启用大模型</span></label><div><label className="label">Provider</label><select className="input" value={form.provider} onChange={event=>providerChanged(event.target.value)}>{providers.map(provider=><option value={provider.value} key={provider.value}>{provider.label}</option>)}</select></div><div><label className="label">Base URL</label><input className="input" value={form.base_url} onChange={event=>setForm({...form,base_url:event.target.value})}/></div><div><label className="label">Model</label><input className="input" value={form.model} onChange={event=>setForm({...form,model:event.target.value})}/></div><div><label className="label">API Key（{form.api_key_configured?"已配置":"未配置"}）</label><input type="password" className="input" autoComplete="new-password" value={form.api_key} placeholder={form.api_key_configured?"留空保留原 Key":"请输入 API Key"} onChange={event=>setForm({...form,api_key:event.target.value})}/></div><div className="flex gap-3"><button disabled={!!busy} className="btn" onClick={()=>action("save-llm",async()=>{const saved=await api<LLMConfig>("/api/settings/llm",{method:"POST",body:JSON.stringify({enabled:form.enabled,provider:form.provider,base_url:form.base_url,model:form.model,api_key:form.api_key||null})});setForm({...saved,api_key:""});return "模型配置已保存。";})}>{busy==="save-llm"?"保存中…":"保存模型配置"}</button><button disabled={!!busy} className="btn bg-slate-700 hover:bg-slate-800" onClick={()=>action("test-llm",async()=>{const result=await api<{success:boolean;error:string;output:string}>("/api/settings/test-llm",{method:"POST"});if(!result.success)throw new Error(result.error);return `模型测试成功：${result.output}`;})}>{busy==="test-llm"?"测试中…":"测试模型"}</button></div></section>
    <section className="card space-y-4"><div><h2 className="font-semibold">Server 酱配置</h2><p className="text-sm text-slate-500">自动流水线不会推送，仅测试或手动确认时真实发送。</p></div><label className="flex items-center gap-3"><input type="checkbox" checked={server.enabled} onChange={event=>setServer({...server,enabled:event.target.checked})}/><span className="text-sm">启用 Server 酱</span></label><div><label className="label">API Base URL</label><input className="input" value={server.api_base} onChange={event=>setServer({...server,api_base:event.target.value})}/></div><div><label className="label">SendKey（{server.sendkey_configured?"已配置":"未配置"}）</label><input type="password" className="input" autoComplete="new-password" value={server.sendkey} placeholder={server.sendkey_configured?"留空保留原 SendKey":"请输入 SendKey"} onChange={event=>setServer({...server,sendkey:event.target.value})}/></div><div className="flex gap-3"><button disabled={!!busy} className="btn" onClick={()=>action("save-push",async()=>{const saved=await api<ServerConfig>("/api/settings/serverchan",{method:"POST",body:JSON.stringify({enabled:server.enabled,api_base:server.api_base,sendkey:server.sendkey||null})});setServer({...server,...saved,sendkey:""});return "Server 酱配置已保存。";})}>{busy==="save-push"?"保存中…":"保存推送配置"}</button><button disabled={!!busy||!server.sendkey_configured} className="btn bg-slate-700 hover:bg-slate-800" onClick={()=>action("test-push",async()=>{await api("/api/settings/test-push",{method:"POST"});await load();return "测试推送成功。";})}>{busy==="test-push"?"推送中…":"测试微信推送"}</button></div></section>
    <section className="card"><h2 className="mb-3 font-semibold">最近推送记录</h2>{server.recent_pushes.length?<div className="space-y-2">{server.recent_pushes.map(item=><div className="flex flex-wrap items-center justify-between gap-2 border-b py-2 text-sm last:border-0" key={item.id}><span>{item.week} · {new Date(item.created_at).toLocaleString()}</span><StatusBadge status={item.status}/>{item.error_message&&<span className="w-full text-xs text-amber-700">{item.error_message}</span>}</div>)}</div>:<p className="text-sm text-slate-500">暂无推送记录。</p>}</section>
    <section className="card"><h2 className="font-semibold">定时任务</h2><p className="mt-2 text-sm text-slate-600">默认每周一 08:30（Asia/Shanghai）生成周报；不会自动真实推送。</p></section>
  </div>;
}
