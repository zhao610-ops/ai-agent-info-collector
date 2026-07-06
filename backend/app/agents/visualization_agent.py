from pathlib import Path

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.config import get_settings
from app.services.keyword_service import get_keyword_history
from app.tools.chart_tool import ChartTool


class VisualizationAgent(BaseAgent):
    name = "VisualizationAgent"

    def run(self, session: Session, week: str, context: dict) -> dict:
        output_dir = Path(get_settings().reports_dir) / week
        tool = ChartTool(output_dir)
        frequencies = {item["keyword"]: item["frequency"] for item in context["trends"]}
        history = get_keyword_history(session, [item["keyword"] for item in context["trends"][:5]])
        tasks = {
            "wordcloud_image": lambda: tool.wordcloud(frequencies),
            "github_chart_image": lambda: tool.github_growth(context["repos"]),
            "keyword_trend_image": lambda: tool.keyword_trend(history),
        }
        result = {}
        errors = []
        # 三张图相互隔离，单张失败只记录错误，不阻断周报生成。
        for field, task in tasks.items():
            try:
                result[field] = task()
            except Exception as exc:
                result[field] = ""
                errors.append(f"{field} 生成失败：{exc}")
        if errors:
            context["fallbacks"].extend(errors)
            context["agent_errors"].setdefault(self.name, []).extend(errors)
        result["_output_count"] = sum(bool(result[field]) for field in tasks)
        return result
