import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.config import get_settings
from app.database import PushLog
from app.services.settings_service import get_serverchan_config
from app.tools.serverchan_tool import ServerChanTool


class ServerChanPushAgent(BaseAgent):
    name = "ServerChanPushAgent"

    def run(self, session: Session, week: str, context: dict) -> dict:
        config = get_serverchan_config(session, include_secret=True)
        title = f"AI Agent 周报｜{week}"
        top_words = "、".join(item["keyword"] for item in context["trends"][:5])
        repos = "\n".join(f'{i}. {row["full_name"]}：+{row["stars_growth_7d"]}' for i, row in enumerate(context["repos"][:3], 1))
        desp = f'## 本周核心判断\n\n{context["report"]["summary"]}\n\n## 本周热词\n\n{top_words}\n\n## GitHub 热门项目\n\n{repos}\n\n## 完整周报\n\n{get_settings().frontend_url}/reports/{week}'
        # 定时和一键生成流程不自动真实推送，只有显式推送或测试操作才允许发送。
        if not context.get("allow_push", False):
            status, response, error = "skipped", {}, "等待用户确认推送"
        elif not config["enabled"] or not config["sendkey_configured"]:
            status, response, error = "skipped", {}, "Server 酱未启用或未配置 SendKey"
        else:
            try:
                response = ServerChanTool(config["api_base"], config["sendkey"]).push(title, desp)
                status, error = "success", ""
            except Exception as exc:
                status, response, error = "failed", {}, str(exc)
        log = PushLog(week=week, title=title, content=desp, status=status,
                      response=json.dumps(response, ensure_ascii=False), error_message=error,
                      pushed_at=datetime.now() if status == "success" else None)
        session.add(log); session.commit()
        return {"status": status, "error": error}
