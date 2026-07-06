import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.agents.serverchan_push_agent import ServerChanPushAgent
from app.database import GithubRepo, KeywordStat, WeeklyReport, get_db


router = APIRouter(prefix="/api", tags=["reports"])


def report_dict(row: WeeklyReport, detail: bool = False) -> dict:
    data = {"id": row.id, "week": row.week, "title": row.title, "summary": row.summary,
            "wordcloud_image": row.wordcloud_image, "github_chart_image": row.github_chart_image,
            "keyword_trend_image": row.keyword_trend_image, "generation_mode": row.generation_mode,
            "llm_provider": row.llm_provider, "llm_model": row.llm_model,
            "created_at": row.created_at, "pushed_at": row.pushed_at,
            "push_status": row.push_status}
    if detail:
        data.update({"content_md": row.content_md, "content_html": row.content_html})
    return data


@router.get("/reports")
def reports(session: Session = Depends(get_db)):
    return [report_dict(row) for row in session.query(WeeklyReport).order_by(WeeklyReport.created_at.desc()).all()]


@router.get("/reports/{week}")
def report_detail(week: str, session: Session = Depends(get_db)):
    row = session.query(WeeklyReport).filter(WeeklyReport.week == week).first()
    if not row: raise HTTPException(404, "周报不存在")
    return report_dict(row, detail=True)


@router.post("/reports/{week}/push")
def push_report(week: str, session: Session = Depends(get_db)):
    # 手动推送只使用已经生成并保存的数据，避免重新执行整套周报任务。
    report = session.query(WeeklyReport).filter(WeeklyReport.week == week).first()
    if not report:
        raise HTTPException(404, "周报不存在")
    if report.pushed_at:
        raise HTTPException(409, "该周报已经推送过，不能重复推送")

    trends = session.query(KeywordStat).filter(KeywordStat.week == week).order_by(KeywordStat.trend_score.desc()).all()
    repos = session.query(GithubRepo).filter(GithubRepo.week == week).order_by(GithubRepo.stars_growth_7d.desc()).limit(10).all()
    context = {
        "allow_push": True,
        "report": {"summary": report.summary},
        "trends": [{"keyword": row.keyword} for row in trends],
        "repos": [{"full_name": row.full_name, "stars_growth_7d": row.stars_growth_7d} for row in repos],
    }

    # 复用当前自动任务的微信配置和推送实现，并只在真实发送成功后标记已推送。
    result = ServerChanPushAgent().run(session, week, context)
    if result["status"] != "success":
        raise HTTPException(502, result["error"] or "微信推送失败")
    report.pushed_at = datetime.now()
    report.push_status = "success"
    session.commit()
    return {"message": "周报已成功推送到微信", "week": week, "pushed_at": report.pushed_at}


@router.get("/reports/{week}/images/{image_name}")
def report_image(week: str, image_name: str, session: Session = Depends(get_db)):
    if image_name not in {"wordcloud.png", "github_growth_top10.png", "keyword_trend.png"}:
        raise HTTPException(404, "图片不存在")
    row = session.query(WeeklyReport).filter(WeeklyReport.week == week).first()
    if not row: raise HTTPException(404, "周报不存在")
    path = Path(row.report_path).parent / image_name
    if not path.exists(): raise HTTPException(404, "图片不存在")
    return FileResponse(path)


@router.get("/github/hot")
def github_hot(week: str | None = None, session: Session = Depends(get_db)):
    if not week:
        latest_report = session.query(WeeklyReport.week).order_by(WeeklyReport.created_at.desc()).first()
        latest = latest_report or session.query(GithubRepo.week).order_by(GithubRepo.created_at.desc()).first()
        week = latest[0] if latest else ""
    rows = session.query(GithubRepo).filter(GithubRepo.week == week).order_by(GithubRepo.stars_growth_7d.desc()).limit(10).all()
    return [{"week": row.week, "repo_name": row.repo_name, "full_name": row.full_name, "url": row.url,
             "description": row.description, "language": row.language, "stars": row.stars,
             "forks": row.forks, "open_issues": row.open_issues, "stars_growth_7d": row.stars_growth_7d,
             "topics": json.loads(row.topics)} for row in rows]


@router.get("/keywords/trends")
def keyword_trends(week: str | None = None, session: Session = Depends(get_db)):
    if not week:
        latest_report = session.query(WeeklyReport.week).order_by(WeeklyReport.created_at.desc()).first()
        latest = latest_report or session.query(KeywordStat.week).order_by(KeywordStat.week.desc()).first()
        week = latest[0] if latest else ""
    rows = session.query(KeywordStat).filter(KeywordStat.week == week).order_by(KeywordStat.trend_score.desc()).all()
    return [{"week": row.week, "keyword": row.keyword, "frequency": row.frequency,
             "source_count": row.source_count, "github_count": row.github_count, "news_count": row.news_count,
             "growth_rate": row.growth_rate, "trend_score": row.trend_score} for row in rows]
