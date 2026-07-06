import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.agents.orchestrator_agent import OrchestratorAgent
from app.database import AgentRun, SessionLocal, get_db


router = APIRouter(prefix="/api/agents", tags=["agents"])
logger = logging.getLogger(__name__)


def _run_weekly() -> None:
    session = SessionLocal()
    try:
        OrchestratorAgent().run(session)
    except Exception:
        # 后台任务异常已由 Orchestrator 写入数据库，此处兜底避免异常影响服务进程。
        session.rollback()
        logger.exception("手动周报任务执行失败")
    finally:
        session.close()


@router.post("/run-weekly", status_code=202)
def run_weekly(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_weekly)
    return {"status": "accepted", "message": "周报任务已提交"}


@router.get("/runs")
def list_runs(limit: int = 100, session: Session = Depends(get_db)):
    rows = session.query(AgentRun).order_by(AgentRun.started_at.desc()).limit(min(limit, 500)).all()
    return [{"id": row.id, "run_id": row.run_id, "week": row.week, "agent_name": row.agent_name,
             "status": row.status, "input": row.input, "output": row.output, "error": row.error,
             "output_count": row.output_count, "duration_ms": row.duration_ms,
             "started_at": row.started_at, "finished_at": row.finished_at} for row in rows]
