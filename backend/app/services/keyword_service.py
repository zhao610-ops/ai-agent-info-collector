import re
from collections import Counter
from datetime import datetime, timedelta

import jieba
from sqlalchemy.orm import Session

from app.database import KeywordStat


STOPWORDS = {"这个", "一个", "进行", "使用", "通过", "相关", "项目", "系统", "能力", "开始", "成为", "正在", "可以", "智能", "人工智能"}
ALIASES = {"agent": "Agent", "agents": "Agent", "multi-agent": "Multi-Agent", "workflow": "Workflow", "mcp": "MCP", "rag": "RAG", "llm": "LLM"}


def extract_keywords(texts: list[str], top_n: int = 30) -> Counter:
    counter: Counter = Counter()
    for text in texts:
        normalized = re.sub(r"[^\w\-\u4e00-\u9fff]+", " ", text.lower())
        for token in jieba.cut(normalized):
            word = token.strip()
            if len(word) < 2 or word in STOPWORDS or word.isdigit():
                continue
            counter[ALIASES.get(word, word)] += 1
    return Counter(dict(counter.most_common(top_n)))


def save_keyword_stats(session: Session, week: str, frequencies: Counter, news_texts: list[str], repo_texts: list[str]) -> list[dict]:
    previous_rows = session.query(KeywordStat).filter(KeywordStat.week < week).order_by(KeywordStat.week.desc()).all()
    previous = {}
    for row in previous_rows:
        previous.setdefault(row.keyword, row.frequency)
    session.query(KeywordStat).filter(KeywordStat.week == week).delete()
    results = []
    for keyword, frequency in frequencies.items():
        news_count = sum(keyword.lower() in text.lower() for text in news_texts)
        github_count = sum(keyword.lower() in text.lower() for text in repo_texts)
        old = previous.get(keyword, 0)
        growth_rate = ((frequency - old) / old * 100) if old else (100.0 if frequency else 0)
        trend_score = round(frequency * 0.7 + max(growth_rate, 0) * 0.03, 2)
        row = KeywordStat(keyword=keyword, week=week, frequency=frequency,
                          source_count=news_count + github_count, github_count=github_count,
                          news_count=news_count, growth_rate=round(growth_rate, 2), trend_score=trend_score)
        session.add(row)
        results.append({"keyword": keyword, "frequency": frequency, "source_count": row.source_count,
                        "github_count": github_count, "news_count": news_count,
                        "growth_rate": row.growth_rate, "trend_score": trend_score})
    session.commit()
    return sorted(results, key=lambda item: item["trend_score"], reverse=True)


def _previous_week(week: str, offset: int) -> str:
    """将 ISO 周字符串转换为前 N 周，避免依赖平台相关的 strptime 指令。"""
    year_text, week_text = week.split("-W", 1)
    monday = datetime.fromisocalendar(int(year_text), int(week_text), 1) - timedelta(weeks=offset)
    iso = monday.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def ensure_keyword_history(session: Session, week: str, trends: list[dict], history_weeks: int = 6) -> None:
    """真实历史不足四周时，为当前热门词补齐六周可复现的 mock 趋势。"""
    keywords = [item["keyword"] for item in trends[:5]]
    if not keywords:
        return
    existing_weeks = {
        row[0] for row in session.query(KeywordStat.week).filter(
            KeywordStat.week < week,
            KeywordStat.keyword.in_(keywords),
        ).distinct().all()
    }
    if len(existing_weeks) >= 4:
        return
    trend_rows = trends[:5]
    for offset in range(history_weeks, 0, -1):
        history_week = _previous_week(week, offset)
        for index, item in enumerate(trend_rows):
            exists = session.query(KeywordStat.id).filter(
                KeywordStat.week == history_week,
                KeywordStat.keyword == item["keyword"],
            ).first()
            if exists:
                continue
            # 使用稳定波动构造升降温曲线，相同周次重复运行不会产生重复记录。
            base = max(item["frequency"] - (history_weeks - offset), 1)
            frequency = max(base + ((offset + index) % 3) - 1, 1)
            session.add(KeywordStat(
                keyword=item["keyword"], week=history_week, frequency=frequency,
                source_count=frequency, github_count=max(frequency // 2, 0),
                news_count=max(frequency - frequency // 2, 0), growth_rate=0,
                trend_score=round(frequency * 0.7, 2),
            ))
    session.commit()


def get_keyword_history(session: Session, keywords: list[str], limit_weeks: int = 8) -> list[dict]:
    """返回最多八周的关键词频次，供趋势折线图使用。"""
    if not keywords:
        return []
    weeks = [
        row[0] for row in session.query(KeywordStat.week)
        .filter(KeywordStat.keyword.in_(keywords))
        .distinct().order_by(KeywordStat.week.desc()).limit(limit_weeks).all()
    ]
    rows = session.query(KeywordStat).filter(
        KeywordStat.keyword.in_(keywords),
        KeywordStat.week.in_(weeks),
    ).order_by(KeywordStat.week.asc()).all()
    return [{"week": row.week, "keyword": row.keyword, "frequency": row.frequency} for row in rows]
