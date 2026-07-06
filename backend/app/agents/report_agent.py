from pathlib import Path

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.config import get_settings
from app.services.report_service import build_template_report, save_report_file, to_html
from app.services.settings_service import get_llm_config
from app.tools.llm_tool import LLMTool


class ReportAgent(BaseAgent):
    name = "ReportAgent"

    def run(self, session: Session, week: str, context: dict) -> dict:
        summary, template = build_template_report(week, context["articles"], context["repos"], context["trends"])
        config = get_llm_config(session, include_secret=True)
        content = template
        mode = "template"
        llm_error = ""
        if config["enabled"] and config["api_key_configured"]:
            try:
                prompt = "请基于以下可靠素材生成中文 AI Agent 周报。保留所有原始链接，不编造事实，使用清晰 Markdown，包含核心结论、重要新闻、GitHub TOP10、热词、趋势判断和项目启发。\n\n" + template
                content = LLMTool(config["base_url"], config["model"], config["api_key"]).chat([
                    {"role": "system", "content": "你是严谨的 AI Agent 行业分析师。"},
                    {"role": "user", "content": prompt},
                ])
                mode = "llm"
                first_paragraph = next((line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")), summary)
                summary = first_paragraph[:500]
            except Exception as exc:
                llm_error = str(exc)
                context["fallbacks"].append(f"ReportAgent 大模型降级：{exc}")
                context["agent_errors"].setdefault(self.name, []).append(f"LLM 调用失败，已降级模板周报：{exc}")
        report_dir = Path(get_settings().reports_dir) / week
        path = save_report_file(report_dir, content)
        return {"summary": summary, "content_md": content, "content_html": to_html(content),
                "report_path": path, "generation_mode": mode, "llm_error": llm_error,
                "llm_enabled": config["enabled"], "llm_provider": config["provider"], "llm_model": config["model"],
                "_output_count": 1}
