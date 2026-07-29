# QuizMasterPro V2 — 通用万能刷题系统

<div align="center">

**📚 上传即用 · 智能复习 · 模拟考试 · 数据洞察**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

## 📖 项目简介

**QuizMasterPro V2** 是一个**万能通用刷题系统**——不管你要备考什么考试，只需要把题库文件（Word/PDF/ZIP）拖进去，系统自动解析、分类，提供智能复习建议和模拟考试功能。

核心设计理念：**一次上传，终身使用**。所有刷题数据本地存储，无需联网，无需注册。

### 🚀 零配置开箱即用

项目提供打包好的 **单文件 .exe 程序**，下载即可运行：

```
📥 下载 QuizMasterProV2.exe → 双击运行 → 浏览器自动打开 → 开始刷题
```

- ✅ **无需安装 Python**，无需配置任何环境
- ✅ **无需安装数据库**，SQLite 内嵌
- ✅ **无需联网**
- ✅ 所有数据保存在 .exe 同级的 `data/` 文件夹
- ✅ U 盘拷走即用，换电脑数据也一起带走

> 📦 .exe 文件就在仓库 `dist/` 目录中，直接下载即可。如果你更习惯从源码运行，请看下方。

### 🎯 适用场景

| 场景 | 举例 |
|------|------|
| 🏫 **学校考试** | 期中期末、课程测验、知识点复习 |
| 📝 **各类资格证书** | 教师资格证、建造师、会计、医学等 |
| 🎓 **升学考试** | 考研政治、考公行测、专升本 |
| 🏢 **企业内部考核** | 安全培训、合规考试、产品知识 |
| 📖 **任何有题库的考试** | 只要题目能整理成 docx/pdf/txt |

---

## ✨ 核心功能

### 🔍 智能题库解析
- 支持 **Word (.docx)** / **PDF** / **TXT** / **ZIP 压缩包** 一键上传
- 自动识别**判断题、单选题、多选题**三种题型
- 支持按**学科文件夹**组织 ZIP，自动拆分科目
- 解析结果即时生成，无需手动整理

### 📊 个性化数据看板
- **总览面板**：总题量、已学题目、正确率、待复习数、掌握度分布
- **学科 × 题型交叉矩阵**：一眼看清每个科目的弱项
- **每日趋势图**：14 天正确率和答题量走势
- **错题排行榜**：顽固错题一目了然

### 🧠 间隔重复算法 (Spaced Repetition)
- 基于**掌握度等级（0-5 级）**自动计算复习间隔
- 复习间隔：当天 → 1天 → 3天 → 7天 → 14天 → 30天
- 答错立即降级回 0，确保薄弱点反复强化
- 智能优先级排序：`错题数 × 10 + 逾期天数 × 4 + 时间衰减`

### 📝 多种刷题模式
| 模式 | 说明 |
|------|------|
| **智能复习** | 按算法推荐最需要复习的题目 |
| **顺序练习** | 按题库原始顺序逐题练习 |
| **随机模式** | 随机抽取，打乱顺序 |
| **错题优先** | 专门攻克错题，适合考前冲刺 |
| **学科筛选** | 选择特定学科集中练习 |
| **题型筛选** | 只练单选题 / 多选题 / 判断题 |

### 🏆 模拟考试
- 自定义**题量、时间、及格线**
- 实时倒计时，模拟真实考试压力
- **题型分布**自动匹配实际考试比例
- 交卷后详细分析：各题型得分率、错题明细
- 历史成绩追踪，查看进步曲线

### 💡 AI 智能复习建议 (V2 增强版)
- **阶段感知**：根据距离考试天数（>14天 / 7-14天 / 3-7天 / 1-3天 / 当天）给出不同策略
- **趋势分析**：对比近 3 天 vs 前期正确率，判断进步/退步/稳定
- **薄弱环节诊断**：按题型维度分析，标记高/中/低优先级
- **考试准备度评分**：综合进度、正确率、趋势、薄弱项、时间压力的 0-100 分评估
- **每日练习计划**：自动计算各题型配额，薄弱项加权多练

### 🌓 深色模式
- 支持浅色/深色主题一键切换
- 精心调校的色彩系统，长时间刷题不累眼
- 偏好自动记忆

### 📦 便携打包
- 支持 PyInstaller 打包为**单文件 .exe**
- 数据目录放在 exe 旁边，U 盘带走即用
- 无需安装 Python 环境

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    QuizMasterPro V2                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐    ┌────────────────────────────┐ │
│  │   前端 (SPA)      │    │      后端 (FastAPI)         │ │
│  │                  │    │                            │ │
│  │  • 原生 HTML/CSS │◄──►│  • 题目解析引擎             │ │
│  │  • 香草 JS       │    │  • 间隔重复算法             │ │
│  │  • 响应式布局     │    │  • 复习建议引擎             │ │
│  │  • Chart.js 绑图  │    │  • 模拟考试系统             │ │
│  │                  │    │  • RESTful API              │ │
│  └──────────────────┘    └───────────┬────────────────┘ │
│                                       │                   │
│                          ┌────────────▼────────────────┐ │
│                          │     数据层                   │ │
│                          │                             │ │
│                          │  • SQLite (本地数据库)        │ │
│                          │  • questions.js (题库文件)    │ │
│                          │  • 文件系统 (上传文件)        │ │
│                          └─────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI 0.116.1 | 高性能异步 Web 框架 |
| **数据库 ORM** | SQLAlchemy 2.0+ | 操作 SQLite |
| **文档解析** | python-docx, pdfplumber, PyPDF2 | 多格式题库解析 |
| **前端** | 原生 HTML/CSS/JS | 零依赖 SPA，Chart.js CDN |
| **打包** | PyInstaller 6.0+ | 单文件 exe 分发 |
| **服务器** | Uvicorn | ASGI 高性能服务器 |

### 数据库设计

```
┌─────────────────┐   ┌──────────────────┐   ┌───────────────────┐
│    Record        │   │   ExamResult      │   │   SubjectConfig    │
├─────────────────┤   ├──────────────────┤   ├───────────────────┤
│ qid (PK)        │   │ id (PK, auto)     │   │ subject (PK)       │
│ wrong           │   │ subject           │   │ subject_name       │
│ correct         │   │ subject_name      │   │ exam_date          │
│ streak          │   │ score             │   │ pass_line          │
│ mastery (0-5)   │   │ pass_line         │   └───────────────────┘
│ last            │   │ passed            │
│ next            │   │ single/multi/     │   ┌───────────────────┐
│ last_pick       │   │ judge_got/total   │   │   DailyStats       │
└─────────────────┘   │ detail            │   ├───────────────────┤
                      │ created_at        │   │ id (PK, auto)      │
                      └──────────────────┘   │ date               │
                                             │ subject            │
                                             │ total_answered     │
                                             │ total_correct      │
                                             │ accuracy           │
                                             └───────────────────┘
```

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Windows / macOS / Linux

### 方式一：使用 EXE（推荐 ✨ 无需配置）

1. 从仓库 `dist/` 目录下载 `QuizMasterProV2.exe`
2. 双击运行
3. 浏览器自动打开 → 开始刷题

> 就是这么简单。不需要装 Python，不需要装数据库，不需要联网。

### 方式二：从源码运行（开发者）

```bash
# 1. 克隆仓库
git clone https://github.com/Charlie-xl-max/QuizMasterProV2.git
cd QuizMasterProV2

# 2. 安装依赖
conda create -n py39 python=3.9
conda activate py39
pip install -r requirements.txt

# 3. 启动
python main.py
```

浏览器自动打开 `http://localhost:8080`。

### 上传题库

1. 点击页面右上角 **📤 上传题库**
2. 选择你的题库文件（`.docx` / `.pdf` / `.zip`）
3. 系统自动解析并加载
4. 开始刷题！

> **局域网共享**：启动后终端会显示局域网 IP，同一 WiFi 下的手机/平板也能访问！

---

## 📁 题库格式说明

### 支持的题库格式

系统期望题库按以下格式组织。无论是 `.docx`、`.pdf` 还是 `.txt`，里面的文本结构都遵循相同规范：

```
判断题
二进制数 1010 转换为十进制是 10。
【答案】对

单选题
以下哪个不是操作系统的核心功能？
A. 进程管理
B. 内存管理
C. 数据库查询
D. 文件管理
【答案】C

多选题
以下哪些属于计算机网络的拓扑结构？
A. 星型
B. 总线型
C. 数据库型
D. 环型
【答案】ABD
```

### 答案标记格式

| 格式 | 示例 |
|------|------|
| `【答案】A` | ✅ 支持 |
| `[答案] A` | ✅ 支持 |
| `答案：A` | ✅ 支持 |
| `参考答案: A` | ✅ 支持 |
| `正确答案：A` | ✅ 支持 |

### ZIP 压缩包组织方式

**方式一：按学科分文件夹**（推荐——系统自动识别学科名称）

```
题库.zip
├── 计算机网络/
│   ├── 判断题.docx
│   ├── 单选题.docx
│   └── 多选题.docx
├── 数据结构/
│   ├── 第一章.pdf
│   └── 第二章.pdf
└── 操作系统/
    └── 全部题目.txt
```

**方式二：扁平结构**（所有题目合并为一个科目）

```
题库.zip
├── 题目1.docx
├── 题目2.pdf
└── 题目3.txt
```

---

## 📡 API 文档

启动服务后访问 `http://localhost:8080/docs` 查看 Swagger 交互式 API 文档。

### 核心接口一览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/upload` | 上传题库文件 |
| `POST` | `/api/parse` | 手动触发解析 |
| `GET` | `/api/bank_info` | 获取题库概览 |
| `POST` | `/api/record` | 提交答题记录 |
| `GET` | `/api/review_queue` | 获取复习队列 |
| `GET` | `/api/stats` | 获取统计数据 |
| `GET` | `/api/daily_stats` | 获取每日趋势 |
| `GET` | `/api/review_suggestion/{subject}` | 复习建议 V1 |
| `GET` | `/api/review_suggestion_v2/{subject}` | 复习建议 V2（增强版） |
| `GET` | `/api/review_suggestion_all` | 全部科目总览建议 |
| `POST` | `/api/exam_result` | 保存模拟考试成绩 |
| `GET` | `/api/exam_results` | 查询历史成绩 |
| `POST` | `/api/subject_configs` | 设置学科配置 |
| `DELETE` | `/api/subject/{id}` | 删除指定学科 |
| `DELETE` | `/api/bank/clear` | 清空全部数据 |

### 示例请求

```bash
# 提交一条答题记录
curl -X POST http://localhost:8080/api/record \
  -H "Content-Type: application/json" \
  -d '{"qid": "network_single_0001", "isCorrect": true}'

# 获取复习建议
curl http://localhost:8080/api/review_suggestion_v2/network

# 获取统计数据
curl http://localhost:8080/api/stats
```

---

## 🔧 打包为 EXE

```bash
python build_exe.py
```

打包完成后，`dist/QuizMasterProV2.exe` 即为免安装单文件程序。双击运行，数据自动保存在 exe 同级 `data/` 目录。

---

## 📂 项目结构

```
QuizMasterProV2/
├── main.py                # FastAPI 主程序（1227 行）
│   ├── 数据模型定义        # Record / ExamResult / SubjectConfig / DailyStats
│   ├── 间隔重复算法        # priority() 函数
│   ├── 答题记录 API        # /api/record, /api/review_queue ...
│   ├── 模拟考试 API        # /api/exam_result ...
│   ├── 复习建议 API        # /api/review_suggestion_v2 ...
│   ├── 题库管理 API        # /api/upload, /api/bank_info ...
│   └── 应用启动入口        # uvicorn + 浏览器自动打开
│
├── question_parser.py     # 题库解析引擎（697 行）
│   ├── 文本提取            # docx / pdf / txt
│   ├── 题目检测与分割      # 判断题 / 单选题 / 多选题
│   ├── 答案与选项提取      # 正则匹配多种格式
│   ├── ZIP 层级解析       # 支持学科文件夹
│   └── questions.js 生成  # 标准化 JSON 输出
│
├── index.html             # 前端 SPA（85KB）
│   ├── 设计令牌系统        # CSS 变量，支持深色模式
│   ├── 统计看板            # 总览 / 学科 / 题型矩阵
│   ├── 智能建议面板        # 趋势 / 薄弱项 / 每日计划
│   ├── 刷题界面            # 多种模式，即时反馈
│   ├── 模拟考试            # 倒计时 / 自动批改 / 成绩分析
│   ├── 图表可视化          # Chart.js 趋势图
│   └── 设置面板            # 学科配置 / 考试日期 / 数据管理
│
├── questions.js           # 题库数据文件（自动生成）
├── build_exe.py           # PyInstaller 打包脚本
└── requirements.txt       # Python 依赖
```

---

## 🧪 复习算法详解

### 掌握度模型

```
答对 → 掌握度 +1 → 复习间隔跃升
答错 → 掌握度 = 0 → 立即重新复习

Level 0: 当天复习       (刚做错或新题)
Level 1: 1 天后复习
Level 2: 3 天后复习
Level 3: 7 天后复习
Level 4: 14 天后复习
Level 5: 30 天后复习     (已彻底掌握)
```

### 优先级公式

```
priority = wrong × 10 + overdue × 4 + days_since × 0.5
         + (5 - mastery) × 2 + streak_penalty(5)

其中:
  wrong       = 累计错误次数 → 错得多优先
  overdue     = 逾期天数 → 该复习的题优先
  days_since  = 距上次复习天数 → 太久没看的也提权
  mastery     = 掌握度 → 不熟悉的优先
  streak_penalty = 连对中断惩罚 → 曾经错但最近对的也要复习
```

### 考试准备度评分

综合评估五个维度：

1. **学习进度** (0-25分)：已答题数的百分比
2. **正确率** (0-25分)：以 60% 为基准线
3. **薄弱项惩罚** (0-15分)：高优先级薄弱题型扣分
4. **趋势加减** (±10分)：正确率上升/下降趋势
5. **时间压力** (±5分)：距离考试的时间充裕度

---

## 🎨 界面预览

- **暖色纸张风格**：模拟真实纸质试卷的阅读感受
- **Fraunces + Noto Serif SC** 字体搭配，优雅且护眼
- **深色模式**：低亮度环境下自动适配
- **响应式布局**：桌面 / 平板 / 手机均可使用

---

## 🔒 数据安全

- **100% 本地运行**：所有数据保存在本地 SQLite 和文件中
- **无需联网**：不依赖任何云服务，不上传任何数据
- **数据可迁移**：`data/` 目录包含全部刷题记录，复制即可迁移

---

## 📝 著作权与许可

```
Copyright (c) 2026 QuizMasterPro V2 Contributors
```

本项目基于 **MIT License** 开源发布，详见 [LICENSE](LICENSE) 文件。

你可以自由地：
- ✅ 使用、复制、修改、合并、发布、分发
- ✅ 用于个人、商业或教育目的
- ✅ 将代码集成到你自己的项目中

唯一要求：
- 📋 保留原始版权声明和许可声明

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) — 现代化的 Python Web 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) — Python SQL 工具包
- [python-docx](https://python-docx.readthedocs.io/) — Word 文档解析
- [pdfplumber](https://github.com/jsvine/pdfplumber) — PDF 文本提取
- [Chart.js](https://www.chartjs.org/) — 前端图表库

---

<div align="center">

**Made with ❤️ for lifelong learners**

</div>
