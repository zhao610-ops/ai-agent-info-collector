from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(200), default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[str] = mapped_column(Text, default="[]")
    category: Mapped[str] = mapped_column(String(100), default="news")
    relevance_score: Mapped[float] = mapped_column(Float, default=0)
    heat_score: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class GithubRepo(Base):
    __tablename__ = "github_repos"
    id: Mapped[int] = mapped_column(primary_key=True)
    week: Mapped[str] = mapped_column(String(10), index=True)
    repo_name: Mapped[str] = mapped_column(String(300))
    full_name: Mapped[str] = mapped_column(String(300), index=True)
    url: Mapped[str] = mapped_column(String(1000))
    description: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(100), default="")
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    open_issues: Mapped[int] = mapped_column(Integer, default=0)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    stars_growth_7d: Mapped[int] = mapped_column(Integer, default=0)
    topics: Mapped[str] = mapped_column(Text, default="[]")
    agent_relevance_score: Mapped[float] = mapped_column(Float, default=0)
    heat_score: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class KeywordStat(Base):
    __tablename__ = "keyword_stats"
    id: Mapped[int] = mapped_column(primary_key=True)
    keyword: Mapped[str] = mapped_column(String(200), index=True)
    week: Mapped[str] = mapped_column(String(10), index=True)
    frequency: Mapped[int] = mapped_column(Integer, default=0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    github_count: Mapped[int] = mapped_column(Integer, default=0)
    news_count: Mapped[int] = mapped_column(Integer, default=0)
    growth_rate: Mapped[float] = mapped_column(Float, default=0)
    trend_score: Mapped[float] = mapped_column(Float, default=0)


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    week: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text, default="")
    content_md: Mapped[str] = mapped_column(Text)
    content_html: Mapped[str] = mapped_column(Text)
    wordcloud_image: Mapped[str] = mapped_column(String(500), default="")
    github_chart_image: Mapped[str] = mapped_column(String(500), default="")
    keyword_trend_image: Mapped[str] = mapped_column(String(500), default="")
    report_path: Mapped[str] = mapped_column(String(500), default="")
    llm_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    llm_provider: Mapped[str] = mapped_column(String(100), default="")
    llm_model: Mapped[str] = mapped_column(String(200), default="")
    generation_mode: Mapped[str] = mapped_column(String(20), default="template")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    push_status: Mapped[str] = mapped_column(String(30), default="not_pushed")


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String(50), index=True)
    week: Mapped[str] = mapped_column(String(10), index=True)
    agent_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="running")
    input: Mapped[str] = mapped_column(Text, default="")
    output: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    output_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PushLog(Base):
    __tablename__ = "push_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    week: Mapped[str] = mapped_column(String(10), index=True)
    channel: Mapped[str] = mapped_column(String(50), default="serverchan")
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30))
    response: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str] = mapped_column(Text, default="")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AppSetting(Base):
    __tablename__ = "settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, default="")
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


settings = get_settings()
if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.removeprefix("sqlite:///")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    # create_all 不会更新已有表，因此建表后执行轻量兼容迁移。
    Base.metadata.create_all(engine)
    from app.services.migration_service import migrate_schema
    migrate_schema(engine)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
