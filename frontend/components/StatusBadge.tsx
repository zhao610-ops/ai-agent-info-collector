const styles: Record<string, string> = {
  success: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  running: "bg-blue-50 text-blue-700 ring-blue-200",
  pending: "bg-amber-50 text-amber-700 ring-amber-200",
  failed: "bg-red-50 text-red-700 ring-red-200",
  skipped: "bg-slate-100 text-slate-600 ring-slate-200",
  not_pushed: "bg-slate-100 text-slate-600 ring-slate-200",
};

export function StatusBadge({ status }: { status: string }) {
  // 未知状态采用中性色，避免后端扩展状态后页面失去样式。
  const className = styles[status] || "bg-slate-100 text-slate-700 ring-slate-200";
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${className}`}>{status}</span>;
}
