import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Article
from app.tools.rss_tool import RSSTool
from app.agents.base_agent import BaseAgent


class NewsAgent(BaseAgent):
    name = "NewsAgent"

    def run(self, session: Session, week: str, context: dict) -> list[dict]:
        settings = get_settings()
        tool = RSSTool()
        try:
            items = tool.fetch([url.strip() for url in settings.news_rss_urls.split(",") if url.strip()])
            items = [item for item in items if item.get("title") and item.get("url")]
            if not items:
                raise RuntimeError("RSS 未返回数据")
        except Exception as exc:
            items = tool.mock()
            context["fallbacks"].append("NewsAgent 使用 mock 数据")
            context["agent_errors"].setdefault(self.name, []).append(f"RSS 采集失败，已使用 mock 数据：{exc}")
        result = []
        for item in items:
            try:
                published = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00")).replace(tzinfo=None) if item.get("published_at") else None
            except (TypeError, ValueError):
                published = None
            row = session.query(Article).filter(Article.url == item["url"]).first()
            if not row:
                row = Article(title=item["title"], url=item["url"], source=item["source"], published_at=published,
                              summary=item.get("summary", ""), keywords=json.dumps([], ensure_ascii=False),
                              relevance_score=80, heat_score=60)
                session.add(row)
            result.append({**item, "published_at": item.get("published_at")})
        session.commit()
        return result
