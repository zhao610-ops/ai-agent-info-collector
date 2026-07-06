# AI Agent Weekly Radar｜多 Agent 协作的 AI 行业情报周报系统

一个可完整演示的 AI Agent 工程项目：每周采集 AI Agent 新闻与 GitHub 热门项目，完成清洗、趋势分析、可视化和中文周报生成，并通过前端展示 7 个 Agent 的执行状态。系统支持 OpenAI 兼容模型和 Server 酱；没有任何 API Key 时也能依靠 mock 与模板降级跑通闭环。

## 项目亮点

- 7 个 Agent 顺序协作，统一记录 pending、running、success、failed、耗时、输出数量和异常。
- RSS、GitHub、LLM、图表和推送均有隔离或降级策略，单个外部服务失败不会退出 FastAPI。
- jieba 分词、停用词过滤、历史周对比，并在数据不足时补齐 6 周 mock 趋势。
- 自动生成词云、GitHub Star 增长榜和关键词趋势图。
- 支持 DeepSeek、Qwen、Kimi、SiliconFlow 和自定义 OpenAI 兼容模型。
- API Key 与 SendKey 只保存在环境变量或数据库，查询接口只返回“是否已配置”。
- 自动流水线只生成周报，不真实推送；微信推送必须由用户测试或手动确认。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Next.js 16、React 19、TypeScript、Tailwind CSS |
| 后端 | FastAPI、SQLAlchemy、Pydantic Settings、APScheduler |
| 数据分析 | jieba、pandas |
| 可视化 | Matplotlib、WordCloud |
| 外部能力 | RSS、GitHub REST API、OpenAI Compatible Chat Completions、Server 酱 |
| 存储与测试 | SQLite、pytest |

## 系统架构

```mermaid
flowchart LR
    UI[Next.js 管理前端] --> API[FastAPI API]
    API --> O[OrchestratorAgent]
    O --> N[NewsAgent]
    N --> G[GitHubAgent]
    G --> T[TrendAgent]
    T --> V[VisualizationAgent]
    V --> R[ReportAgent]
    R --> P[ServerChanPushAgent]
    N --> DB[(SQLite)]
    G --> DB
    T --> DB
    O --> DB
    V --> FS[reports/{week}/]
    R --> FS
    API --> DB
    API --> FS
```

## 多 Agent 执行流程

1. `OrchestratorAgent` 创建运行批次及全部 pending 日志。
2. `NewsAgent` 读取 RSS；失败时使用 mock 新闻。
3. `GitHubAgent` 调用公开 API或 Token API；失败时使用 mock 项目。
4. `TrendAgent` 分词、过滤停用词、统计频次并对比历史周数据。
5. `VisualizationAgent` 独立生成三张图，单张失败不会阻断后续步骤。
6. `ReportAgent` 优先调用 LLM；失败或未配置时生成模板周报。
7. `ServerChanPushAgent` 在自动流水线中记录 skipped，不发起真实推送。

每次运行都会在 `agent_runs` 中保存状态、输入摘要、输出摘要、输出数量、错误、开始时间、结束时间和耗时。

## 功能模块

- **Dashboard**：最新结论、最近运行、热词、热门项目、一键运行及手动微信推送。
- **Reports**：历史周报、生成模式、使用模型、推送状态。
- **Report Detail**：Markdown 转换后的正文及三张图表。
- **Agents**：7 个 Agent 执行链路和历史运行记录。
- **GitHub**：Stars、Forks、增长、语言、Topics、热度分和相关度分。
- **Settings**：LLM 与 Server 酱配置、模型测试、测试推送及推送日志。

## 快速启动

推荐 Python 3.11/3.12、Node.js 20+。

### 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

首次启动会创建数据库；已有 SQLite 会自动补齐新增字段。生成文件位于 `backend/reports/{week}/`。

### 前端

```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

访问：http://localhost:3000

## 环境变量

后端配置见 `backend/.env.example`，前端配置见 `frontend/.env.local.example`。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `BACKEND_PORT` | `8000` | uvicorn 启动端口参考值 |
| `DATABASE_URL` | `sqlite:///./data/weekly_agent.db` | 数据库连接 |
| `REPORTS_DIR` | `./reports` | 周报和图表目录 |
| `FRONTEND_URL` | `http://localhost:3000` | 周报链接及 CORS 来源 |
| `GITHUB_TOKEN` | 空 | 可选，提高 GitHub API 限额 |
| `NEWS_RSS_URLS` | Google News RSS | 多地址使用逗号分隔 |
| `LLM_ENABLED` | `false` | 是否启用 LLM |
| `LLM_PROVIDER` | `deepseek` | 模型提供商 |
| `LLM_API_KEY` | 空 | 模型密钥 |
| `LLM_BASE_URL` | 空 | OpenAI 兼容 API 地址 |
| `LLM_MODEL` | 空 | 模型名称 |
| `SERVER_CHAN_ENABLED` | `false` | 是否允许显式推送 |
| `SERVER_CHAN_SENDKEY` | 空 | Server 酱 SendKey |
| `SERVER_CHAN_API_BASE` | `https://sctapi.ftqq.com` | Server 酱 API 地址 |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | 前端请求的后端地址 |

不要提交 `.env`、`.env.local`、数据库或生成目录。

## LLM 配置

可在 Settings 页面选择 DeepSeek、Qwen、Kimi、SiliconFlow 或 Custom，填写 Base URL、Model 和 API Key。后端使用 OpenAI Compatible `/chat/completions`。

- 密钥输入框为空时保存，会保留原 Key。
- GET 接口不返回密钥明文。
- 模型未配置、关闭或调用失败时，`ReportAgent` 自动使用模板，并将 `generation_mode` 记录为 `template`。
- “测试模型”会真实调用所配置的模型服务。

## Server 酱配置

1. 从 Server 酱获取 SendKey。
2. 在 Settings 页面启用 Server 酱并填写 SendKey，或写入后端 `.env`。
3. 保存后页面只显示“已配置”，不会回显明文。
4. “测试微信推送”和 Dashboard 的“确认推送微信”会真实发送。
5. 定时任务和“手动运行周报”只生成周报，`push_logs` 记录 skipped，不会自动发送。

推送失败最多重试 3 次，并记录状态、错误和重试次数。

## Mock 与异常兜底

| 故障 | 处理方式 |
| --- | --- |
| RSS 不可用 | 使用内置 mock 新闻 |
| GitHub API 不可用 | 使用 10 个 mock 项目 |
| 历史趋势不足 | 自动补齐 6 周 mock 关键词数据 |
| LLM 不可用 | 使用模板生成中文周报 |
| 单张图表失败 | 记录错误，其他图表和周报继续生成 |
| Server 酱未配置 | 写入 skipped 推送日志，不报错退出 |
| 后台任务异常 | 写入 Agent 日志，FastAPI 继续运行 |

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/agents/run-weekly` | 提交周报任务 |
| GET | `/api/agents/runs` | Agent 运行记录 |
| GET | `/api/reports` | 历史周报 |
| GET | `/api/reports/{week}` | 周报详情 |
| POST | `/api/reports/{week}/push` | 确认推送指定周报 |
| GET | `/api/github/hot` | GitHub 热门项目 |
| GET | `/api/keywords/trends` | 关键词趋势 |
| GET/POST | `/api/settings/llm` | 查询/保存模型配置 |
| POST | `/api/settings/test-llm` | 测试模型 |
| GET/POST | `/api/settings/serverchan` | 查询/保存推送配置 |
| POST | `/api/settings/test-push` | 测试微信推送 |

## 三分钟演示流程

1. **0:00–0:30**：打开 Dashboard，说明系统采集、分析、生成和展示的闭环。
2. **0:30–1:10**：点击“手动运行周报”，进入 Agents 页面展示 7 个 Agent 的顺序、状态、耗时和输出数量。
3. **1:10–1:50**：进入 Reports，打开最新周报，展示 LLM/Template 标记、正文、词云、GitHub 增长图和历史趋势图。
4. **1:50–2:20**：进入 GitHub 页面，展示项目增长、热度和 Agent 相关度。
5. **2:20–2:50**：进入 Settings，说明模型多 Provider、密钥脱敏、模板降级和 Server 酱显式推送策略。
6. **2:50–3:00**：总结“多 Agent 编排、可观测、可降级、可配置”的工程价值。

## 验收说明

### 无任何 Key 的 mock 闭环

确保 `.env` 中 `GITHUB_TOKEN`、`LLM_API_KEY`、`SERVER_CHAN_SENDKEY` 为空，并将 `LLM_ENABLED=false`、`SERVER_CHAN_ENABLED=false`，启动前后端后点击“手动运行周报”。

验收结果：

- Agents 页面出现 7 个 Agent，最终状态为 success。
- Reports 页面出现新周报，生成方式为 template。
- `backend/reports/{week}/` 包含 `report.md`、`wordcloud.png`、`github_growth_top10.png`、`keyword_trend.png`。
- Settings 最近推送记录显示 skipped，微信不会收到消息。

### 自动化检查

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe -c "from pathlib import Path; [compile(p.read_text(encoding='utf-8'), str(p), 'exec') for p in Path('app').rglob('*.py')]"

cd ..\frontend
.\node_modules\.bin\tsc.cmd --noEmit --incremental false
npm.cmd run build

cd ..
git diff --check
```

模型测试和 Server 酱测试会访问真实外部服务，验收时按需执行。

## 简历写法参考

**AI Agent Weekly Radar｜多 Agent 协作的 AI 行业情报周报系统**

基于 FastAPI、Next.js 和 SQLAlchemy 设计并实现 7 Agent 情报分析流水线，完成 RSS/GitHub 数据采集、jieba 趋势分析、Matplotlib/WordCloud 可视化、OpenAI 兼容模型周报生成及 Server 酱微信推送；构建统一 Agent 运行日志，记录状态、耗时、输出量和异常，并通过 mock、模板降级、图表隔离与推送重试保证无外部 Key 时仍可完整演示。

可拆分为简历要点：

- 设计 Orchestrator 驱动的 7 Agent 顺序编排和可观测状态模型，实现任务级错误追踪与耗时统计。
- 集成多 Provider OpenAI Compatible API，构建 LLM 失败自动降级模板的周报生成链路。
- 实现关键词历史趋势、GitHub 增长分析和三类图表，支持 4～8 周趋势可视化。
- 通过外部服务 mock、后台异常兜底、密钥脱敏和显式推送策略提升系统稳定性与安全性。

## 面试讲解话术

“这个项目不是简单的定时脚本，而是一条可观测、可降级的多 Agent 数据流水线。Orchestrator 会先创建完整执行队列，再依次调用新闻、GitHub、趋势、可视化、报告和推送 Agent。每一步统一记录状态、耗时、输出数量和异常。外部服务失败不会直接打断流程：RSS 和 GitHub 使用 mock，LLM 降级模板，图表逐张隔离，未配置 Server 酱则记录 skipped。前端能够展示完整执行链路、历史周报、趋势图和配置状态。工程上重点解决了任务可观测性、外部依赖不稳定、密钥安全和可重复演示问题。”

## 后续优化方向

- 引入 Celery/RQ 与 Redis，将进程内后台任务升级为可靠任务队列。
- 使用 Alembic 管理正式数据库迁移。
- 增加 RSS 来源管理、数据质量指标和可配置评分权重。
- 增加 OpenTelemetry、结构化日志和告警。
- 增加 Docker Compose 与 CI 流水线。
- 在确有需求时再扩展鉴权、多用户和 RAG，避免当前阶段过度设计。
