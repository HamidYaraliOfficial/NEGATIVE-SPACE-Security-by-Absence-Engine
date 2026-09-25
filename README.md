# NEGATIVE SPACE — Security by Absence Engine

*A behavioral security platform that asks a different question: not "what suspicious thing was seen?" but "what should have been seen, and why has it gone quiet?"*

**Stack:** Rust + eBPF-ready host sensor · Python (FastAPI) detection engine · PostgreSQL · Next.js/TypeScript observatory UI
**Languages:** English · فارسی (Persian) · 中文 (Chinese) — each section below is written natively in that language, with full RTL support for Persian and LTR for English/Chinese in the UI.

---

## 🇬🇧 English

### What this is

NEGATIVE SPACE builds an **Expected Reality Model** for every host, service, process, API, database, scheduled job, authentication flow, log source, and security control in your environment. It learns what *should* happen — a heartbeat every 30 seconds, a nightly backup job, a service that always talks to a specific database — and then treats the **unexpected disappearance** of that pattern as a first-class security signal, on equal footing with a positive alert.

It is not a log monitor or a SIEM. It is an intelligence layer that continuously diffs **expected reality vs. observed reality**, in time, in relationships, and in workflow structure — and tells you, with full evidence and confidence scoring, when a silence is meaningful.

### Architecture

| Layer | Language | Responsibility |
|---|---|---|
| **Host Sensor** | Rust | Process lifecycle, network connection, and heartbeat telemetry; bounded memory, offline spooling, privacy filtering (hash/drop sensitive fields), backpressure. Ships metadata-only canonical events. Designed with a clean seam to swap the polling collectors for a real `aya`-based eBPF collector on Linux (see `agent-rust/src/collectors/mod.rs`). |
| **Detection Engine** | Python (FastAPI) | Baseline learning (EWMA/CUSUM/percentiles), Temporal Silence Analyzer, Data Availability Confidence Layer, Relationship Graph diffing, Incident Correlation, Business Hours / Maintenance Window engine, REST + WebSocket API. |
| **Storage** | PostgreSQL | Entities, expected signals, observations, detections, relationships, incidents, cases, agents, business hours, audit log, and a partitioned `events` table for raw evidence. |
| **Observatory UI** | Next.js + TypeScript + Tailwind | Overview, Silence Explorer, Relationship Graph, Incident Center, Agent Management, Business Hours, Reports. Windows 11–inspired Fluent/acrylic design system with Light, Dark, AMOLED, Windows-Blue and Red accent themes. Full English / Persian (RTL) / Chinese localization and a global command palette (Ctrl+K). |

### Repository structure

```
negative-space/
├── agent-rust/           # Rust host sensor
│   ├── src/collectors/   # process, network, heartbeat collectors
│   └── config/agent.toml # secure-by-default agent config
├── backend-python/        # FastAPI detection engine + API
│   └── app/
│       ├── core/          # baseline, silence analyzer, confidence, graph, business hours...
│       ├── api/            # REST + WebSocket routes
│       └── db/             # SQLAlchemy models + schema.sql
├── frontend/               # Next.js observatory UI
│   └── src/{app,components,i18n,lib}/
├── docker-compose.yml
└── .env.example
```

### Installation

**Option A — Docker Compose (recommended for evaluation)**

```bash
cp .env.example .env
# edit .env — set POSTGRES_PASSWORD and JWT_SECRET to real values
docker compose up --build
```

This starts PostgreSQL, Redis, NATS, the backend on `http://localhost:8000`, and the frontend on `http://localhost:3000`.

Create your first admin user:

```bash
docker compose exec backend python -m scripts.create_admin admin@example.com "a-strong-password"
```

**Option B — Run each component manually**

1. **PostgreSQL** — create a database and apply the schema:
   ```bash
   psql -U postgres -c "CREATE DATABASE negative_space;"
   psql -U postgres -d negative_space -f backend-python/app/db/schema.sql
   ```

2. **Backend**
   ```bash
   cd backend-python
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp ../.env.example .env   # adjust DATABASE_URL etc.
   python -m scripts.create_admin admin@example.com "a-strong-password"
   uvicorn app.main:app --reload --port 8000
   ```

3. **Frontend**
   ```bash
   cd frontend
   npm install
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   echo "NEXT_PUBLIC_WS_URL=ws://localhost:8000" >> .env.local
   npm run dev
   ```
   Open `http://localhost:3000`, sign in, and switch language/theme from the top bar.

4. **Rust agent** (Linux host you want to monitor)
   ```bash
   cd agent-rust
   cargo build --release
   # edit config/agent.toml — set backend.url and backend.enrollment_token
   sudo ./target/release/negspace-agent --config config/agent.toml
   ```

### Business hours & maintenance windows

Go to **Business Hours** in the UI. For any entity (or globally), enter a weekly open schedule (per-day start/end times). The system continuously computes and displays, live:
- whether the entity is **open right now**,
- if closed, the **exact time of the next opening**,
- and **how long** that next window will last.

Windows flagged as *maintenance windows* automatically suppress detections raised during that period — the suppression itself is recorded as evidence, never silently dropped.

### Notes on eBPF

The Rust agent ships with a portable, polling-based collector (`sysinfo` + `/proc`) so it builds and runs anywhere. On Linux with `CAP_BPF` and kernel ≥ 5.8, replace the process/network collectors with an `aya`-based eBPF program attached to `sched_process_exec`, `sched_process_exit`, and `inet_sock_set_state` tracepoints for true in-kernel, zero-poll collection — the `CanonicalEvent` contract is the stable seam, so nothing downstream needs to change.

### License

Provided as a reference implementation for you to extend. Add your own license file before distributing.

---

## 🇮🇷 فارسی

### این پروژه چیست؟

**نگتیو اسپیس** برای هر Host، سرویس، Process، API، دیتابیس، Job زمان‌بندی‌شده، فرآیند احراز هویت، منبع لاگ و کنترل امنیتی، یک **مدل واقعیت مورد انتظار** می‌سازد. سیستم یاد می‌گیرد چه چیزی *باید* اتفاق بیفتد — مثلاً یک Heartbeat هر ۳۰ ثانیه، یک Backup شبانه، یا یک سرویس که همیشه با یک دیتابیس مشخص در ارتباط است — و سپس **ناپدید شدن غیرمنتظره** این الگو را به عنوان یک سیگنال امنیتی درجه‌یک، هم‌تراز با یک هشدار مثبت، در نظر می‌گیرد.

این ابزار یک Log Monitor یا SIEM ساده نیست؛ یک لایه هوشمند است که به‌طور پیوسته **واقعیت مورد انتظار** را با **واقعیت مشاهده‌شده** — از نظر زمانی، رابطه‌ای و ساختار Workflow — مقایسه می‌کند و با شواهد کامل و امتیاز اطمینان، به شما می‌گوید چه زمانی یک سکوت واقعاً معنادار است.

### معماری

| لایه | زبان | مسئولیت |
|---|---|---|
| **Host Sensor** | Rust | جمع‌آوری Telemetry از Process Lifecycle، اتصالات شبکه و Heartbeat؛ حافظه محدود، صف آفلاین، فیلتر حریم خصوصی (Hash/حذف فیلدهای حساس)، Backpressure. فقط Metadata ارسال می‌شود. با یک نقطه اتصال تمیز طراحی شده تا بعداً با یک Collector واقعی مبتنی بر eBPF (کتابخانه `aya`) در لینوکس جایگزین شود. |
| **Detection Engine** | Python (FastAPI) | یادگیری Baseline (EWMA/CUSUM/Percentile)، Temporal Silence Analyzer، لایه اطمینان از در دسترس بودن داده، مقایسه Graph روابط، همبستگی رخدادها، موتور ساعات کاری/پنجره تعمیرات، API با REST و WebSocket. |
| **Storage** | PostgreSQL | Entityها، سیگنال‌های مورد انتظار، مشاهدات، تشخیص‌ها، روابط، رخدادها، پرونده‌ها، عامل‌ها، ساعات کاری، Audit Log و یک جدول Partitioned برای رویدادهای خام. |
| **Observatory UI** | Next.js + TypeScript + Tailwind | صفحات نمای کلی، کاوشگر سکوت، گراف روابط، مرکز رخدادها، مدیریت عامل‌ها، ساعات کاری و گزارش‌ها. طراحی با الهام از ویندوز ۱۱ (Fluent/Acrylic) با تم‌های روشن، تیره، AMOLED و رنگ‌های تاکیدی آبی ویندوز و قرمز. پشتیبانی کامل از سه زبان انگلیسی، فارسی (راست‌چین) و چینی، به همراه پالت فرمان سراسری (Ctrl+K). |

### ساختار مخزن

```
negative-space/
├── agent-rust/           # سنسور Host به زبان Rust
│   ├── src/collectors/   # Collectorهای process، network، heartbeat
│   └── config/agent.toml # تنظیمات پیش‌فرض امن Agent
├── backend-python/        # موتور تشخیص و API با FastAPI
│   └── app/
│       ├── core/          # baseline، تحلیل‌گر سکوت، اطمینان، گراف، ساعات کاری...
│       ├── api/            # مسیرهای REST و WebSocket
│       └── db/             # مدل‌های SQLAlchemy و schema.sql
├── frontend/               # رابط کاربری Observatory با Next.js
│   └── src/{app,components,i18n,lib}/
├── docker-compose.yml
└── .env.example
```

### نصب و راه‌اندازی

**روش A — Docker Compose (پیشنهادی برای تست)**

```bash
cp .env.example .env
# فایل .env را ویرایش کنید — مقدار POSTGRES_PASSWORD و JWT_SECRET را واقعی تنظیم کنید
docker compose up --build
```

این دستور PostgreSQL، Redis، NATS، بک‌اند را روی `http://localhost:8000` و فرانت‌اند را روی `http://localhost:3000` اجرا می‌کند.

ساخت اولین کاربر ادمین:

```bash
docker compose exec backend python -m scripts.create_admin admin@example.com "a-strong-password"
```

**روش B — اجرای دستی هر بخش**

۱. **PostgreSQL** — ساخت دیتابیس و اعمال Schema:
   ```bash
   psql -U postgres -c "CREATE DATABASE negative_space;"
   psql -U postgres -d negative_space -f backend-python/app/db/schema.sql
   ```

۲. **بک‌اند**
   ```bash
   cd backend-python
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp ../.env.example .env   # مقادیر DATABASE_URL و غیره را تنظیم کنید
   python -m scripts.create_admin admin@example.com "a-strong-password"
   uvicorn app.main:app --reload --port 8000
   ```

۳. **فرانت‌اند**
   ```bash
   cd frontend
   npm install
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   echo "NEXT_PUBLIC_WS_URL=ws://localhost:8000" >> .env.local
   npm run dev
   ```
   آدرس `http://localhost:3000` را باز کنید، وارد شوید و زبان/تم را از نوار بالا تغییر دهید.

۴. **Agent مبتنی بر Rust** (روی هاست لینوکسی که می‌خواهید مانیتور کنید)
   ```bash
   cd agent-rust
   cargo build --release
   # فایل config/agent.toml را ویرایش کنید — backend.url و backend.enrollment_token را تنظیم کنید
   sudo ./target/release/negspace-agent --config config/agent.toml
   ```

### ساعات کاری و پنجره‌های تعمیرات

به بخش **ساعات کاری** در رابط کاربری بروید. برای هر Entity (یا به‌صورت سراسری)، یک برنامه هفتگی باز بودن (ساعت شروع/پایان برای هر روز) وارد کنید. سیستم به‌صورت لحظه‌ای و پیوسته محاسبه و نمایش می‌دهد:
- آیا Entity **همین الان باز است**،
- در صورت بسته بودن، **زمان دقیق باز شدن بعدی**،
- و **چه مدت** آن بازه بعدی طول می‌کشد.

بازه‌هایی که به‌عنوان *پنجره تعمیرات* علامت‌گذاری شده‌اند، به‌طور خودکار تشخیص‌های ایجادشده در آن بازه را سرکوب می‌کنند — این سرکوب خودش به‌عنوان شواهد ثبت می‌شود، نه اینکه بی‌سروصدا حذف شود.

### نکته‌ای درباره eBPF

Agent با یک Collector قابل حمل و مبتنی بر Polling (با استفاده از `sysinfo` و `/proc`) ارائه می‌شود تا در هر جایی قابل Build و اجرا باشد. در لینوکس با `CAP_BPF` و Kernel نسخه ۵.۸ به بالا، می‌توان Collectorهای Process/Network را با یک برنامه eBPF مبتنی بر کتابخانه `aya` که به Tracepointهای `sched_process_exec`، `sched_process_exit` و `inet_sock_set_state` متصل است جایگزین کرد تا جمع‌آوری واقعی و بدون Polling در سطح Kernel انجام شود — قرارداد `CanonicalEvent` نقطه اتصال ثابت است و نیازی به تغییر در بخش‌های بعدی نیست.

---

## 🇨🇳 中文

### 这是什么

**NEGATIVE SPACE（负空间）** 会为环境中的每一台主机、服务、进程、API、数据库、计划任务、身份验证流程、日志源和安全控件建立一个**预期现实模型**。系统会学习"应该"发生什么——例如每 30 秒一次的心跳、每晚的备份任务、或某个服务总是与特定数据库通信——然后将这种模式的**意外消失**视为与正向告警同等重要的一级安全信号。

它不是一个日志监控工具或简单的 SIEM，而是一个持续对比**预期现实与观测现实**的智能层——在时间、关系和工作流结构三个维度上——并附带完整证据和置信度评分,告诉你何时一次沉默是真正有意义的。

### 架构

| 层级 | 语言 | 职责 |
|---|---|---|
| **主机传感器** | Rust | 采集进程生命周期、网络连接和心跳遥测数据；内存有界、离线缓存队列、隐私过滤（对敏感字段哈希/丢弃）、背压控制。仅上报元数据的规范事件。预留了清晰的扩展接口，可在 Linux 上替换为基于 `aya` 的真正 eBPF 采集器（见 `agent-rust/src/collectors/mod.rs`）。 |
| **检测引擎** | Python（FastAPI） | 基线学习（EWMA/CUSUM/百分位数）、时序静默分析器、数据可用性置信层、关系图差异分析、事件关联、营业时间/维护窗口引擎、REST + WebSocket API。 |
| **存储** | PostgreSQL | 实体、预期信号、观测记录、检测结果、关系、事件、案例、代理、营业时间、审计日志，以及用于原始证据的分区 `events` 表。 |
| **可观测性 UI** | Next.js + TypeScript + Tailwind | 概览、静默浏览器、关系图谱、事件中心、代理管理、营业时间、报告等页面。采用 Windows 11 风格的 Fluent/亚克力设计系统，支持浅色、深色、纯黑（AMOLED）模式，以及 Windows 蓝与红色强调色。完整支持英语／波斯语（从右到左）／中文本地化，并提供全局命令面板（Ctrl+K）。 |

### 仓库结构

```
negative-space/
├── agent-rust/           # Rust 主机传感器
│   ├── src/collectors/   # 进程、网络、心跳采集器
│   └── config/agent.toml # 默认安全的代理配置
├── backend-python/        # 基于 FastAPI 的检测引擎与 API
│   └── app/
│       ├── core/          # 基线、静默分析器、置信度、图谱、营业时间等
│       ├── api/            # REST 与 WebSocket 路由
│       └── db/             # SQLAlchemy 模型与 schema.sql
├── frontend/               # 基于 Next.js 的可观测性 UI
│   └── src/{app,components,i18n,lib}/
├── docker-compose.yml
└── .env.example
```

### 安装步骤

**方式 A —— Docker Compose（推荐用于评估）**

```bash
cp .env.example .env
# 编辑 .env —— 将 POSTGRES_PASSWORD 和 JWT_SECRET 设置为真实值
docker compose up --build
```

该命令会启动 PostgreSQL、Redis、NATS，后端运行于 `http://localhost:8000`，前端运行于 `http://localhost:3000`。

创建第一个管理员账户：

```bash
docker compose exec backend python -m scripts.create_admin admin@example.com "a-strong-password"
```

**方式 B —— 手动运行各组件**

1. **PostgreSQL** —— 创建数据库并应用 schema：
   ```bash
   psql -U postgres -c "CREATE DATABASE negative_space;"
   psql -U postgres -d negative_space -f backend-python/app/db/schema.sql
   ```

2. **后端**
   ```bash
   cd backend-python
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp ../.env.example .env   # 调整 DATABASE_URL 等配置
   python -m scripts.create_admin admin@example.com "a-strong-password"
   uvicorn app.main:app --reload --port 8000
   ```

3. **前端**
   ```bash
   cd frontend
   npm install
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   echo "NEXT_PUBLIC_WS_URL=ws://localhost:8000" >> .env.local
   npm run dev
   ```
   打开 `http://localhost:3000`，登录后可在顶部栏切换语言与主题。

4. **Rust 代理**（部署在你要监控的 Linux 主机上）
   ```bash
   cd agent-rust
   cargo build --release
   # 编辑 config/agent.toml —— 设置 backend.url 与 backend.enrollment_token
   sudo ./target/release/negspace-agent --config config/agent.toml
   ```

### 营业时间与维护窗口

在界面中进入**营业时间**页面。为任意实体（或全局）输入每周的开放时间表（每天的起止时间）。系统会持续实时计算并显示：
- 该实体**此刻是否处于开放状态**；
- 若已关闭，**下一次开放的确切时间**；
- 以及**下一个开放窗口将持续多久**。

被标记为*维护窗口*的时间段会自动抑制该期间产生的检测结果——这一抑制行为本身会被记录为证据，而不会被静默丢弃。

### 关于 eBPF 的说明

Rust 代理默认使用可移植的轮询式采集器（基于 `sysinfo` 与 `/proc`），因此可以在任何环境中构建和运行。在具备 `CAP_BPF` 权限、内核版本 ≥ 5.8 的 Linux 上，可以将进程/网络采集器替换为基于 `aya` 库、挂载到 `sched_process_exec`、`sched_process_exit` 与 `inet_sock_set_state` 探测点的真正 eBPF 程序，实现内核级、零轮询的采集——`CanonicalEvent` 契约是稳定的衔接层，下游代码无需任何改动。
