from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from wordcloud import WordCloud


class ChartTool:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _font_path() -> str | None:
        candidates = [Path("C:/Windows/Fonts/msyh.ttc"), Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")]
        return str(next((path for path in candidates if path.exists()), "")) or None

    @classmethod
    def _font(cls) -> FontProperties | None:
        path = cls._font_path()
        return FontProperties(fname=path) if path else None

    def wordcloud(self, frequencies: dict[str, int]) -> str:
        path = self.output_dir / "wordcloud.png"
        WordCloud(width=1200, height=600, background_color="white", font_path=self._font_path()).generate_from_frequencies(frequencies or {"AI Agent": 1}).to_file(str(path))
        return str(path)

    def github_growth(self, repos: list[dict]) -> str:
        path = self.output_dir / "github_growth_top10.png"
        rows = sorted(repos, key=lambda row: row["stars_growth_7d"]) [-10:]
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh([r["full_name"] for r in rows], [r["stars_growth_7d"] for r in rows], color="#2563eb")
        ax.set_title("GitHub Star 7日增长 TOP10", fontproperties=self._font())
        ax.set_xlabel("Star 增长", fontproperties=self._font())
        fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)
        return str(path)

    def keyword_trend(self, trends: list[dict]) -> str:
        path = self.output_dir / "keyword_trend.png"
        fig, ax = plt.subplots(figsize=(10, 6))
        keywords = list(dict.fromkeys(row["keyword"] for row in trends))[:5]
        weeks = sorted({row["week"] for row in trends})
        values = {(row["week"], row["keyword"]): row["frequency"] for row in trends}
        for keyword in keywords:
            ax.plot(weeks, [values.get((week, keyword), 0) for week in weeks], marker="o", label=keyword)
        if keywords:
            ax.legend(prop=self._font())
        else:
            ax.text(0.5, 0.5, "暂无趋势数据", ha="center", va="center", fontproperties=self._font())
        ax.set_title("关键词近 4～8 周趋势", fontproperties=self._font())
        ax.set_ylabel("出现频次", fontproperties=self._font())
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)
        return str(path)
