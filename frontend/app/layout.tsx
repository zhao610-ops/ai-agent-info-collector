import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = { title: "AI Agent Weekly Radar", description: "多 Agent 协作的 AI 行业情报周报系统" };
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="zh-CN"><body><Nav/><main className="mx-auto max-w-7xl px-6 py-8">{children}</main></body></html>;
}
