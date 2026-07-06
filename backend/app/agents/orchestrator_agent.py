import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agents.github_agent import GitHubAgent
from app.agents.news_agent import NewsAgent
from app.agents.report_agent import ReportAgent
from app.agents.serverchan_push_agent import ServerChanPushAgent
from app.agents.trend_agent import TrendAgent
from app.agents.visualization_agent import VisualizationAgent
from app.database import AgentRun, WeeklyReport


class OrchestratorAgent:
    name = "OrchestratorAgent"
    pipeline_agents = (
        "NewsAgent", "GitHubAgent", "TrendAgent", "VisualizationAgent",
        "ReportAgent", "ServerChanPushAgent",
    )

    def run(self, session: Session, week: str | None = None) -> dict:
        week = week or datetime.now().strftime("%G-W%V")
        run_id = uuid4().hex
        started_at = datetime.now()
        orchestration_log = AgentRun(run_id=run_id, week=week, agent_name=self.name, status="running", input="{}", started_at=started_at)
        # 在流水线开始前创建全部 pending 记录，便于前端实时展示执行队列。
        session.add(orchestration_log)
        session.add_all(AgentRun(run_id=run_id, week=week, agent_name=name, status="pending") for name in self.pipeline_agents)
        session.commit()
        try:
            result = self._run_pipeline(session, run_id, week)
            orchestration_log.status = "success"
            orchestration_log.output = json.dumps(result, ensure_ascii=False)
            orchestration_log.output_count = 1
            return result
        except Exception as exc:
            orchestration_log.status = "failed"
            orchestration_log.error = str(exc)
            # 上游失败时结束尚未执行的 pending 记录，避免状态页长期显示伪运行状态。
            finished_at = datetime.now()
            pending_logs = session.query(AgentRun).filter(
                AgentRun.run_id == run_id,
                AgentRun.status == "pending",
            ).all()
            for pending_log in pending_logs:
                pending_log.status = "failed"
                pending_log.error = f"因上游步骤失败未执行：{exc}"
                pending_log.finished_at = finished_at
            raise
        finally:
            orchestration_log.finished_at = datetime.now()
            orchestration_log.duration_ms = max(int((orchestration_log.finished_at - started_at).total_seconds() * 1000), 0)
            session.commit()

    def _run_pipeline(self, session: Session, run_id: str, week: str) -> dict:
        # 自动流水线只生成报告，不主动真实推送；推送必须由用户显式确认。
        context = {"fallbacks": [], "allow_push": False}
        context["articles"] = NewsAgent().execute(session, run_id, week, context)
        context["repos"] = GitHubAgent().execute(session, run_id, week, context)
        context["trends"] = TrendAgent().execute(session, run_id, week, context)
        context["charts"] = VisualizationAgent().execute(session, run_id, week, context)
        context["report"] = ReportAgent().execute(session, run_id, week, context)
        report_data = context["report"]
        report = session.query(WeeklyReport).filter(WeeklyReport.week == week).first()
        values = {
            "title": f"AI Agent 周报｜{week}", "summary": report_data["summary"],
            "content_md": report_data["content_md"], "content_html": report_data["content_html"],
            **context["charts"], "report_path": report_data["report_path"],
            "llm_enabled": report_data["llm_enabled"], "llm_provider": report_data["llm_provider"],
            "llm_model": report_data["llm_model"], "generation_mode": report_data["generation_mode"],
        }
        if report:
            for key, value in values.items(): setattr(report, key, value)
        else:
            report = WeeklyReport(week=week, **values); session.add(report)
        session.commit()
        context["push"] = ServerChanPushAgent().execute(session, run_id, week, context)
        if context["push"]["status"] == "success":
            report.pushed_at = datetime.now()
            report.push_status = "success"
            session.commit()
        elif context["push"]["status"] == "skipped":
            report.push_status = "not_pushed"
            session.commit()
        return {"run_id": run_id, "week": week, "report_id": report.id,
                "generation_mode": report.generation_mode, "fallbacks": context["fallbacks"],
                "push": context["push"]}
