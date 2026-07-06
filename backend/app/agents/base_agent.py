import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.database import AgentRun


class BaseAgent:
    name = "BaseAgent"

    def execute(self, session: Session, run_id: str, week: str, context: dict) -> Any:
        # 优先接管 Orchestrator 预创建的 pending 记录，保证前端可观察完整状态变化。
        log = session.query(AgentRun).filter(
            AgentRun.run_id == run_id,
            AgentRun.agent_name == self.name,
            AgentRun.status == "pending",
        ).first()
        if not log:
            log = AgentRun(run_id=run_id, week=week, agent_name=self.name, status="pending")
            session.add(log)
        log.status = "running"
        log.input = json.dumps(self.summarize_input(context), ensure_ascii=False, default=str)
        log.started_at = datetime.now()
        session.commit()
        try:
            result = self.run(session, week, context)
            log.status = "success"
            log.output = json.dumps(self.summarize_output(result), ensure_ascii=False, default=str)
            log.output_count = self.count_output(result)
            # 降级属于成功完成，但仍将原始异常写入日志，便于前端解释数据来源。
            agent_errors = context.get("agent_errors", {}).get(self.name, [])
            if agent_errors:
                log.error = "\n".join(str(error) for error in agent_errors)
            return result
        except Exception as exc:
            log.status = "failed"
            log.error = str(exc)
            raise
        finally:
            log.finished_at = datetime.now()
            log.duration_ms = max(int((log.finished_at - log.started_at).total_seconds() * 1000), 0)
            session.commit()

    def run(self, session: Session, week: str, context: dict) -> Any:
        raise NotImplementedError

    @staticmethod
    def summarize_input(context: dict) -> dict:
        return {key: len(value) if isinstance(value, list) else str(value)[:200] for key, value in context.items()}

    @staticmethod
    def summarize_output(result: Any) -> Any:
        if isinstance(result, list):
            return {"count": len(result)}
        if isinstance(result, dict):
            return {key: value for key, value in result.items() if not key.startswith("_")}
        return result

    @staticmethod
    def count_output(result: Any) -> int:
        """将不同 Agent 的返回值归一为前端可展示的输出数量。"""
        if result is None:
            return 0
        if isinstance(result, (list, tuple, set)):
            return len(result)
        if isinstance(result, dict) and isinstance(result.get("_output_count"), int):
            return result["_output_count"]
        if isinstance(result, dict) and isinstance(result.get("count"), int):
            return result["count"]
        return 1
