from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.agents.base_agent import BaseAgent
from app.database import AgentRun, Base
from app.services.migration_service import migrate_schema


class DemoAgent(BaseAgent):
    """测试 Agent 只返回固定数据，不访问任何外部服务。"""

    name = "DemoAgent"

    def run(self, session, week, context):
        return ["a", "b", "c"]


def test_agent_reuses_pending_log_and_records_metrics():
    # 使用内存数据库验证 pending 到 success 的完整状态转换。
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    session.add(AgentRun(run_id="run-1", week="2026-W27", agent_name="DemoAgent", status="pending"))
    session.commit()

    result = DemoAgent().execute(session, "run-1", "2026-W27", {})
    log = session.query(AgentRun).one()

    assert result == ["a", "b", "c"]
    assert log.status == "success"
    assert log.output_count == 3
    assert log.duration_ms >= 0
    assert log.finished_at is not None


def test_existing_database_schema_is_migrated(tmp_path):
    # 模拟旧版数据库，验证迁移能幂等补齐简历展示所需字段。
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE weekly_reports (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE agent_runs (id INTEGER PRIMARY KEY)"))

    migrate_schema(engine)
    migrate_schema(engine)

    inspector = inspect(engine)
    report_columns = {column["name"] for column in inspector.get_columns("weekly_reports")}
    run_columns = {column["name"] for column in inspector.get_columns("agent_runs")}
    assert "push_status" in report_columns
    assert {"output_count", "duration_ms"}.issubset(run_columns)
