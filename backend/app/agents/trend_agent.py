from sqlalchemy.orm import Session

from app.services.keyword_service import ensure_keyword_history, extract_keywords, save_keyword_stats
from app.agents.base_agent import BaseAgent


class TrendAgent(BaseAgent):
    name = "TrendAgent"

    def run(self, session: Session, week: str, context: dict) -> list[dict]:
        news_texts = [f'{row["title"]} {row["summary"]}' for row in context["articles"]]
        repo_texts = [f'{row["full_name"]} {row["description"]} {" ".join(row["topics"])}' for row in context["repos"]]
        trends = save_keyword_stats(session, week, extract_keywords(news_texts + repo_texts), news_texts, repo_texts)
        # 历史不足时补齐演示数据，确保趋势图始终具备跨周对比意义。
        ensure_keyword_history(session, week, trends)
        return trends
