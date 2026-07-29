# QuizMasterPro — 鸿蒙 (HarmonyOS) App 开发方案

> 基于现有 QuizMasterPro V2 Web 版，设计原生鸿蒙移动端应用

---

## 一、总体定位

将 QuizMasterPro 从 **"桌面 Web + 局域网手机访问"** 升级为 **"原生鸿蒙 App + 本地运行"** 的刷题工具。

**核心理念不变**：题库上传即用、本地数据存储、智能复习算法、离线可用。

---

## 二、技术选型

### 2.1 推荐方案：ArkTS 原生开发

| 维度 | 选型 | 理由 |
|------|------|------|
| **开发语言** | ArkTS (TypeScript 超集) | 鸿蒙官方主推语言，生态最完善 |
| **API 版本** | HarmonyOS API 12+ | 支持最新的 Stage 模型 |
| **UI 框架** | ArkUI (声明式) | 类 SwiftUI/Flutter 的声明式写法 |
| **数据持久化** | 关系型数据库 (RDB) + 用户首选项 (Preferences) | 鸿蒙内置，无额外依赖 |
| **文件处理** | 系统文件选择器 + 内置解析引擎 | docx/pdf 解析逻辑迁移到 ArkTS |
| **最低支持** | HarmonyOS NEXT (5.0) / HarmonyOS 4.0 | 覆盖主流鸿蒙设备 |

### 2.2 为什么选 ArkTS 而不用跨平台框架？

| 对比 | ArkTS 原生 | RN/Flutter for HarmonyOS |
|------|-----------|--------------------------|
| 性能 | ⭐⭐⭐⭐⭐ 原生渲染 | ⭐⭐⭐ 桥接损耗 |
| 鸿蒙特性 | ⭐⭐⭐⭐⭐ 完全支持 | ⭐⭐ 受限 |
| 包体积 | ⭐⭐⭐⭐ 较小 | ⭐⭐ 包含运行时 |
| 长期维护 | ⭐⭐⭐⭐⭐ Google/开源 | ⭐⭐⭐⭐ 华为官方 |
| 开发效率 | ⭐⭐⭐ 需学新语言 | ⭐⭐⭐⭐ 复用现有技能 |

**结论**：鸿蒙是长期方向，用 ArkTS 原生开发是最优选择。

---

## 三、架构设计

```
┌──────────────────────────────────────────────────────────┐
│                   QuizMasterPro 鸿蒙版                     │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                   UI 层 (ArkUI)                       │ │
│  │                                                       │ │
│  │  ┌───────┐ ┌──────────┐ ┌───────┐ ┌────────────┐   │ │
│  │  │首页   │ │刷题页     │ │模拟考 │ │数据看板     │   │ │
│  │  │Dashboard│ │Practice  │ │Exam   │ │Analytics   │   │ │
│  │  └───────┘ └──────────┘ └───────┘ └────────────┘   │ │
│  │  ┌───────┐ ┌──────────┐ ┌───────┐ ┌────────────┐   │ │
│  │  │设置   │ │题目导入   │ │错题本 │ │复习计划     │   │ │
│  │  │Settings│ │Import    │ │Wrong  │ │ReviewPlan  │   │ │
│  │  └───────┘ └──────────┘ └───────┘ └────────────┘   │ │
│  └──────────────────────┬───────────────────────────────┘ │
│                          │                                 │
│  ┌──────────────────────▼───────────────────────────────┐ │
│  │                 业务逻辑层                             │ │
│  │                                                       │ │
│  │  • 间隔重复算法 (Spaced Repetition)                    │ │
│  │  • 题库解析引擎 (Question Parser)                      │ │
│  │  • 复习建议引擎 (Review Advisor)                       │ │
│  │  • 模拟考试引擎 (Exam Engine)                          │ │
│  │  • 统计计算器 (Stats Calculator)                       │ │
│  └──────────────────────┬───────────────────────────────┘ │
│                          │                                 │
│  ┌──────────────────────▼───────────────────────────────┐ │
│  │                  数据层                                │ │
│  │                                                       │ │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────────┐    │ │
│  │  │   RDB    │ │Preferences│ │  文件系统          │    │ │
│  │  │ 关系数据库│ │ 键值存储  │ │  (题库文件/导出)   │    │ │
│  │  └──────────┘ └──────────┘ └───────────────────┘    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

### 3.1 与 Web 版的差异

| 方面 | Web 版 | 鸿蒙版 |
|------|--------|--------|
| 运行方式 | 浏览器访问 localhost:8080 | 原生 App 直接启动 |
| 后端分离 | FastAPI + SQLite | 全部内置在 App 内 |
| 题库上传 | Web 表单上传 | 系统文件选择器 / 分享菜单 |
| 题库存储 | questions.js 文件 | 关系数据库 |
| 联网 | 局域网可访问 | 完全离线可用 |

---

## 四、数据库设计（鸿蒙 RDB）

对应 Web 版的 SQLite，鸿蒙版使用关系型数据库 (RDB)：

```sql
-- 题库表
CREATE TABLE questions (
    id          TEXT PRIMARY KEY,   -- e.g. "network_single_0001"
    subject     TEXT NOT NULL,      -- 学科 ID
    subject_name TEXT NOT NULL,     -- 学科名称
    type        TEXT NOT NULL,      -- 'single' | 'multi' | 'judge'
    stem        TEXT NOT NULL,      -- 题干
    options     TEXT,               -- JSON: {"A":"...", "B":"..."}
    answer      TEXT NOT NULL,      -- 正确答案
    sort_order  INTEGER DEFAULT 0   -- 排序
);

-- 答题记录表
CREATE TABLE records (
    qid         TEXT PRIMARY KEY,
    wrong       INTEGER DEFAULT 0,
    correct     INTEGER DEFAULT 0,
    streak      INTEGER DEFAULT 0,
    mastery     INTEGER DEFAULT 0,  -- 0-5 掌握度
    last_review INTEGER DEFAULT 0,  -- 上次复习时间戳
    next_review INTEGER DEFAULT 0,  -- 下次复习时间戳
    last_pick   INTEGER DEFAULT 0
);

-- 模拟考试成绩表
CREATE TABLE exam_results (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    subject       TEXT,
    subject_name  TEXT,
    score         INTEGER,
    pass_line     INTEGER,
    passed        INTEGER,          -- 0/1
    single_got    INTEGER DEFAULT 0,
    single_total  INTEGER DEFAULT 0,
    multi_got     INTEGER DEFAULT 0,
    multi_total   INTEGER DEFAULT 0,
    judge_got     INTEGER DEFAULT 0,
    judge_total   INTEGER DEFAULT 0,
    detail        TEXT,             -- JSON 错题明细
    created_at    INTEGER
);

-- 学科配置表
CREATE TABLE subject_configs (
    subject      TEXT PRIMARY KEY,
    subject_name TEXT,
    exam_date    INTEGER DEFAULT 0,
    pass_line    INTEGER DEFAULT 60
);

-- 每日统计表
CREATE TABLE daily_stats (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT,            -- '2026-07-29'
    subject         TEXT DEFAULT 'all',
    total_answered  INTEGER DEFAULT 0,
    total_correct   INTEGER DEFAULT 0,
    accuracy        REAL DEFAULT 0.0
);
```

---

## 五、功能模块规划

### 5.1 首页仪表盘 (Dashboard)

```
┌────────────────────────────┐
│   QuizMasterPro            │
│   ───────────               │
│   ┌─────┐ ┌─────┐ ┌─────┐ │
│   │ 总题 │ │ 已学 │ │正确率│ │
│   │ 2500 │ │ 1823 │ │ 78% │ │
│   └─────┘ └─────┘ └─────┘ │
│   ┌─────┐ ┌─────┐         │
│   │待复习│ │错题  │         │
│   │  47  │ │  83  │         │
│   └─────┘ └─────┘         │
│                            │
│   📊 近期趋势 [迷你折线图]  │
│                            │
│   💡 智能建议               │
│   "距考试还有12天，建议     │
│    每天刷40道错题..."       │
│                            │
│   📋 学科列表               │
│   ▸ 计算机网络    82% ▸    │
│   ▸ 数据结构      74% ▸    │
│   ▸ 操作系统      91% ▸    │
└────────────────────────────┘
```

### 5.2 刷题页 (Practice)

- **全屏沉浸模式**：一张卡片一道题，左右滑动或点击翻页
- **底部答案栏**：答完后显示对错 + 正确答案 + 选项染色
- **模式切换**：顶部 Tab 切换（智能复习 / 顺序 / 随机 / 错题优先）
- **筛选**：可选学科 + 题型的组合筛选
- **手势操作**：
  - 左滑 = 答错
  - 右滑 = 答对
  - 上滑 = 跳过
  - 双击 = 收藏/标记

### 5.3 模拟考试 (Exam Mode)

- **考试配置**：选题范围、题量、时长、及格线
- **全屏倒计时**：顶部固定计时器，最后 5 分钟变红闪烁
- **答题卡**：底部导航快速跳转，已答/未答/标记状态
- **交卷**：确认弹窗 → 自动批改 → 成绩单
- **成绩分析**：各题型得分率、错题列表、逐题回顾

### 5.4 数据看板 (Analytics)

- **趋势图**：7/14/30 天正确率 & 答题量曲线
- **学科 × 题型矩阵**：热力图展示各科弱项
- **错题排行榜**：错误次数最多的前 20 题
- **学习时长统计**：每日刷题时长

### 5.5 题库导入 (Import)

三种导入方式：

| 方式 | 说明 |
|------|------|
| **文件选择器** | 从手机存储选择 .docx/.pdf/.zip 文件 |
| **分享菜单** | 在微信/QQ/文件管理器中「分享到 QuizMasterPro」 |
| **Wi-Fi 传输** | App 开启临时 HTTP 服务，电脑浏览器上传 |

### 5.6 新增移动端特性

与原 Web 版相比，鸿蒙版新增：

| 特性 | 说明 |
|------|------|
| 🎙️ **语音答题** | 说出答案选项（利用鸿蒙语音识别） |
| 🔔 **复习提醒** | 本地通知，每日定时提醒刷题 |
| 📱 **桌面小组件** | 显示今日待复习数、正确率 |
| 🌙 **阅读模式** | 护眼模式 + 字体大小调节 |
| 📤 **数据导出** | 导出为 PDF 成绩报告 / JSON 备份 |
| 🔄 **多设备同步** | 通过华为云空间同步数据（可选） |
| ⌨️ **折叠屏适配** | 展开时双栏布局（题目 + 统计） |

---

## 六、UI/UX 设计原则

### 6.1 延续 Web 版设计 DNA

- **暖色纸张风格**：米黄底色 + 深棕文字，模拟纸质试卷
- **Fraunces + Noto Serif SC** 字体（可嵌入或使用系统衬线字体替代）
- **深色模式**：自动跟随系统 / 手动切换
- **设计令牌**：CSS 变量映射到 ArkUI 资源文件

### 6.2 移动端适配

- **底部导航栏**：首页 / 刷题 / 考试 / 我的（4 Tab）
- **单手操作**：关键操作（对/错按钮）在屏幕下半区
- **横屏优化**：刷题时选项并排显示，减少滚动
- **手势优先**：复习卡片模式用滑动手势替代按钮点击

### 6.3 页面路由设计

```
TabBar
├── 首页 (Index)
│   ├── → 学科详情
│   │     ├── → 刷题 (带筛选)
│   │     └── → 模拟考试 (带预设)
│   └── → 复习建议详情
├── 刷题 (Practice)
│   ├── → 刷题中 (全屏)
│   └── → 答题结果
├── 考试 (Exam)
│   ├── → 考试配置
│   ├── → 考试中 (全屏)
│   └── → 成绩单
└── 我的 (Profile)
    ├── → 题库管理
    ├── → 错题本
    ├── → 数据看板
    ├── → 数据导出
    └── → 设置
```

---

## 七、核心算法迁移

### 7.1 间隔重复算法

Web 版的 `priority()` 函数直接翻译为 ArkTS：

```typescript
// ArkTS 版本
const INTERVALS = [0, 1, 3, 7, 14, 30]
const DAY = 86400

function priority(rec: Record): number {
  const now = Math.floor(Date.now() / 1000)
  const daysSince = rec.last_review ? (now - rec.last_review) / DAY : 999
  const overdue = rec.next_review ? Math.max(0, (now - rec.next_review) / DAY) : 999
  return (
    rec.wrong * 10 +
    overdue * 4 +
    daysSince * 0.5 +
    (5 - rec.mastery) * 2 +
    (rec.streak === 0 && rec.wrong > 0 ? 5 : 0)
  )
}

function onAnswer(qid: string, isCorrect: boolean): void {
  const now = Math.floor(Date.now() / 1000)
  const rec = getRecord(qid)
  if (isCorrect) {
    rec.correct += 1
    rec.streak += 1
    rec.mastery = Math.min(5, rec.mastery + 1)
    rec.next_review = now + INTERVALS[rec.mastery] * DAY
  } else {
    rec.wrong += 1
    rec.streak = 0
    rec.mastery = 0
    rec.next_review = now
  }
  rec.last_review = now
  rec.last_pick = now
  saveRecord(rec)
  updateDailyStats(now, isCorrect)
}
```

### 7.2 题库解析引擎

原 Python `question_parser.py` 核心逻辑迁移到 ArkTS：

- **文本提取**：`docx` → 使用鸿蒙文件 API 读取 + zip.js 解压 XML；`pdf` → 内置 PDF 解析或调用 pdf.js
- **题目检测**：正则表达式逻辑完全一致，JS 正则原生兼容
- **解析流程**：逐行扫描 → 题型标记检测 → 题干/选项/答案提取
- **难点**：docx/pdf 解析在 ArkTS 中没有现成库，需要：
  - **docx**：手动解压 zip + 解析 `word/document.xml`
  - **pdf**：集成 pdf.js 或使用鸿蒙内置 PDF 能力（受限）
  - **折中方案**：优先支持 .txt 和 .zip(内含 txt)，docx/pdf 可在 Web 端预处理

---

## 八、开发阶段与时间线

```
Phase 1 ████████████░░░░░░░░░░  基础框架 (2-3 周)
Phase 2     ████████████░░░░░░  MVP 发布  (3-4 周)
Phase 3         ████████████░░  功能完善  (3-4 周)
Phase 4             ██████████  增强特性  (2-3 周)
Phase 5               ████████  发布上线  (1-2 周)
```

### Phase 1：基础框架 (2-3 周)

- [ ] 项目初始化：DevEco Studio 创建工程，配置 ArkTS + Stage 模型
- [ ] 数据库层：RDB 建表 + DAO 封装（CRUD 操作）
- [ ] 路由框架：TabBar + Navigation 路由配置
- [ ] 设计令牌系统：颜色/字体/间距资源文件
- [ ] 题库模型定义 + 数据导入接口
- [ ] 基础 UI 组件库：按钮、卡片、统计数字、进度条

### Phase 2：MVP 核心功能 (3-4 周)

- [ ] **首页仪表盘**：统计数据卡片、学科列表、迷你图表
- [ ] **题库导入**：文件选择器 + .txt/.zip 解析引擎
- [ ] **刷题页**：单题卡片、选项交互、对错反馈、掌握度更新
- [ ] **间隔重复算法**：完整移植
- [ ] **刷题模式**：智能复习 / 顺序 / 随机 / 错题优先
- [ ] **学科 & 题型筛选**
- [ ] **深色模式**

### Phase 3：功能完善 (3-4 周)

- [ ] **模拟考试**：配置页 → 考试中 → 自动批改 → 成绩单
- [ ] **数据看板**：趋势图表（内置 Canvas 绑制）、学科×题型矩阵
- [ ] **复习建议引擎**：阶段感知 + 薄弱分析 + 每日计划
- [ ] **错题本**：错题列表、按学科/题型/错误次数筛选
- [ ] **学科 & 题库管理**：配置考试日期、及格线、删除/清空
- [ ] **docx 解析支持**：zip 解压 + XML 解析实现

### Phase 4：增强特性 (2-3 周)

- [ ] **本地通知**：每日复习提醒
- [ ] **数据导出**：JSON 备份 / PDF 报告
- [ ] **桌面小组件**：今日待复习数
- [ ] **折叠屏适配**：展开双栏布局
- [ ] **语音答题**：鸿蒙语音识别集成
- [ ] **Wi-Fi 传输**：App 内建 HTTP 服务接收文件

### Phase 5：测试 & 发布 (1-2 周)

- [ ] 多设备适配测试（手机/平板/折叠屏）
- [ ] 性能优化：题库加载、RDB 查询优化
- [ ] 华为应用市场审核材料准备
- [ ] 隐私政策 & 用户协议
- [ ] 应用截图 & 宣传素材
- [ ] 提交华为应用市场 (AppGallery)

---

## 九、技术风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| **docx/pdf 解析在 ArkTS 中无现成库** | 高 | Phase 2 先支持 .txt，Phase 3 自研 docx 解析，pdf 降级为提醒用户转 txt |
| **鸿蒙 RDB 性能** | 中 | 题库较大时分页加载，索引优化 |
| **ArkUI 复杂动画实现** | 低 | 刷题卡片动画用内置 transition API |
| **DevEco Studio 稳定性** | 中 | 保持更新到最新版本，Git 频繁提交 |
| **鸿蒙 NEXT 向后兼容** | 中 | 最低支持 API 12，用条件编译处理差异 |

---

## 十、与 Web 版的共存策略

鸿蒙版发布后，两版**并行维护**：

```
QuizMasterPro
├── Web 版 (FastAPI + SPA)
│   ├── 桌面端主力使用
│   ├── 题库管理 & 批量导入
│   └── 局域网其他设备访问
│
└── 鸿蒙版 (ArkTS 原生)
    ├── 碎片时间刷题
    ├── 离线可用
    └── 移动端专属体验
```

**数据互通方案**（Phase 4+）：
- 鸿蒙版导出 JSON，Web 版导入
- Web 版导出 JSON，鸿蒙版导入（通过 Wi-Fi 传输）
- 未来可选华为云空间同步

---

## 十一、待确认事项

在正式开发前，建议明确以下几点：

1. **最低支持的鸿蒙版本**：NEXT (5.0) 还是兼容 4.0？
2. **是否需要数据与 Web 版互通**？如果需要，优先开发导入导出
3. **docx/pdf 解析优先级**：是否接受 Phase 2 只支持 txt + zip(txt 内)？
4. **是否需要登录/账号系统**？还是保持纯本地？
5. **上架哪个应用市场**？华为 AppGallery 为主，是否考虑其他？

---

> 本方案为初版设计，可根据实际需求调整。建议先确认上述待确认事项后再进入 Phase 1 开发。
