from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.agents.report_agent as report_agent_module
import app.agents.serverchan_push_agent as push_agent_module
import app.agents.visualization_agent as visualization_agent_module
from app.agents.orchestrator_agent import OrchestratorAgent
from app.database import AgentRun, Base, KeywordStat, PushLog, WeeklyReport
from app.tools.github_tool import GithubTool
from app.tools.llm_tool import LLMTool
from app.tools.rss_tool import RSSTool


def test_mock_pipeline_generates_report_charts_and_agent_logs(tmp_path, monkeypatch):
    # 使用独立数据库和报告目录，强制所有外部服务失败，验证完整降级闭环。
    engine = create_engine(f"sqlite:///{tmp_path / 'pipeline.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    reports_dir = tmp_path / "reports"
    local_settings = SimpleNamespace(reports_dir=str(reports_dir), frontend_url="http://localhost:3000")

    monkeypatch.setattr(RSSTool, "fetch", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("RSS 离线")))
    monkeypatch.setattr(GithubTool, "search", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("GitHub 离线")))
    monkeypatch.setattr(LLMTool, "chat", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("LLM 离线")))
    monkeypatch.setattr(visualization_agent_module, "get_settings", lambda: local_settings)
    monkeypatch.setattr(report_agent_module, "get_settings", lambda: local_settings)
    monkeypatch.setattr(push_agent_module, "get_settings", lambda: local_settings)
    monkeypatch.setattr(report_agent_module, "get_llm_config", lambda *args, **kwargs: {
        "enabled": True, "api_key_configured": True, "api_key": "test-key",
        "provider": "custom", "base_url": "http://invalid", "model": "mock-model",
    })
    monkeypatch.setattr(push_agent_module, "get_serverchan_config", lambda *args, **kwargs: {
        "enabled": False, "sendkey_configured": False, "sendkey": "", "api_base": "",
    })

    result = OrchestratorAgent().run(session, "2026-W27")

    report = session.query(WeeklyReport).filter_by(week="2026-W27").one()
    logs = {row.agent_name: row for row in session.query(AgentRun).filter_by(run_id=result["run_id"]).all()}
    output_counts = {
        "NewsAgent": 5,
        "GitHubAgent": 10,
        "VisualizationAgent": 3,
        "ReportAgent": 1,
        "ServerChanPushAgent": 1,
    }

    assert report.generation_mode == "template"
    assert report.push_status == "not_pushed"
    assert (reports_dir / "2026-W27" / "report.md").exists()
    assert (reports_dir / "2026-W27" / "wordcloud.png").exists()
    assert (reports_dir / "2026-W27" / "github_growth_top10.png").exists()
    assert (reports_dir / "2026-W27" / "keyword_trend.png").exists()
    assert len({row.week for row in session.query(KeywordStat).all()}) >= 7
    assert session.query(PushLog).filter_by(week="2026-W27", status="skipped").count() == 1
    assert len(logs) == 7
    assert all(log.status == "success" for log in logs.values())
    assert logs["TrendAgent"].output_count > 0
    for agent_name, expected_count in output_counts.items():
        assert logs[agent_name].output_count == expected_count
    assert "RSS 离线" in logs["NewsAgent"].error
    assert "GitHub 离线" in logs["GitHubAgent"].error
    assert "LLM 离线" in logs["ReportAgent"].error
    assert "等待用户确认推送" in logs["ServerChanPushAgent"].error
