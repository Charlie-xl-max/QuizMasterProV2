# -*- coding: utf-8 -*-
"""
QuizMasterPro V2 - 通用万能刷题系统
Copyright (c) 2026 QuizMasterPro V2 Contributors
Licensed under the MIT License (see LICENSE file for details)

FastAPI 后端：支持上传 Word/PDF/ZIP 自动解析题库，智能复习建议，模拟考试
"""
import os
import sys
import time
import json
import webbrowser
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker


# ─── 路径工具 ───────────────────────────────────────────
def _get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def _get_data_dir():
    """数据目录始终放在 EXE/脚本旁边，不使用 C 盘"""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


# ─── 常量 ───────────────────────────────────────────────
BASE_DIR = _get_resource_path('')
DATA_DIR = os.path.join(_get_data_dir(), "data")
UPLOAD_DIR = os.path.join(_get_data_dir(), "uploads")
DB_PATH = os.path.join(DATA_DIR, "quiz.db")
QUESTIONS_JS = os.path.join(_get_data_dir(), "questions.js")
FRONTEND_PORT = 8080
DAY = 86400
INTERVALS = [0, 1, 3, 7, 14, 30]

_data_root = _get_data_dir()
os.makedirs(_data_root, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

_db_path_fixed = DB_PATH.replace('\\', '/')
DB_URL = f"sqlite:///{_db_path_fixed}"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# ─── 数据库模型 ─────────────────────────────────────────
class Record(Base):
    __tablename__ = "records"
    qid = Column(String(100), primary_key=True, index=True)
    wrong = Column(Integer, default=0)
    correct = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    mastery = Column(Integer, default=0)
    last = Column(Integer, default=0)
    next = Column(Integer, default=0)
    last_pick = Column(Integer, default=0)

    def to_dict(self):
        return {
            "qid": self.qid, "wrong": self.wrong, "correct": self.correct,
            "streak": self.streak, "mastery": self.mastery,
            "last": self.last, "next": self.next, "last_pick": self.last_pick,
        }


class ExamResult(Base):
    __tablename__ = "exam_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(50), index=True)
    subject_name = Column(String(100))
    score = Column(Integer)
    pass_line = Column(Integer)
    passed = Column(Integer)
    single_got = Column(Integer, default=0)
    single_total = Column(Integer, default=0)
    multi_got = Column(Integer, default=0)
    multi_total = Column(Integer, default=0)
    judge_got = Column(Integer, default=0)
    judge_total = Column(Integer, default=0)
    detail = Column(Text)
    created_at = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id, "subject": self.subject, "subject_name": self.subject_name,
            "score": self.score, "pass_line": self.pass_line, "passed": self.passed,
            "single_got": self.single_got, "single_total": self.single_total,
            "multi_got": self.multi_got, "multi_total": self.multi_total,
            "judge_got": self.judge_got, "judge_total": self.judge_total,
            "detail": self.detail, "created_at": self.created_at,
        }


class SubjectConfig(Base):
    __tablename__ = "subject_configs"
    subject = Column(String(50), primary_key=True)
    subject_name = Column(String(100))
    exam_date = Column(Integer, default=0)
    pass_line = Column(Integer, default=60)

    def to_dict(self):
        return {
            "subject": self.subject, "subject_name": self.subject_name,
            "exam_date": self.exam_date, "pass_line": self.pass_line,
        }


class DailyStats(Base):
    """每日统计 —— 用于趋势分析"""
    __tablename__ = "daily_stats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), index=True)  # "2026-07-25"
    subject = Column(String(50), default="all")
    total_answered = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id, "date": self.date, "subject": self.subject,
            "total_answered": self.total_answered, "total_correct": self.total_correct,
            "accuracy": self.accuracy,
        }


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_initial_bank()


def _ensure_initial_bank():
    if os.path.exists(QUESTIONS_JS):
        return
    src = os.path.join(BASE_DIR, "questions.js")
    if os.path.exists(src):
        import shutil
        shutil.copy2(src, QUESTIONS_JS)


# ─── 复习优先级算法 ─────────────────────────────────────
def priority(rec):
    now = int(time.time())
    days_since = (now - rec.last) / DAY if rec.last else 999
    overdue = max(0, (now - rec.next) / DAY) if rec.next else 999
    return (
        rec.wrong * 10 + overdue * 4 + days_since * 0.5
        + (5 - rec.mastery) * 2 + (5 if rec.streak == 0 and rec.wrong > 0 else 0)
    )


# ─── FastAPI 应用 ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="QuizMasterPro V2", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════
#  API：答题记录
# ═══════════════════════════════════════════════════════

class RecordIn(BaseModel):
    qid: str = None
    questionId: str = None
    isCorrect: bool = None
    correct: bool = None

    @property
    def effective_qid(self):
        return self.qid or self.questionId

    @property
    def effective_is_correct(self):
        if self.isCorrect is not None:
            return self.isCorrect
        return self.correct


@app.post("/api/record")
def api_record(data: RecordIn):
    with SessionLocal() as db:
        now = int(time.time())
        qid = data.effective_qid
        is_correct = data.effective_is_correct
        if not qid or is_correct is None:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        rec = db.query(Record).filter(Record.qid == qid).first()
        if not rec:
            rec = Record(qid=qid, wrong=0, correct=0, streak=0, mastery=0,
                         last=0, next=0, last_pick=0)
        if is_correct:
            rec.correct += 1
            rec.streak += 1
            rec.mastery = min(5, rec.mastery + 1)
            rec.next = now + INTERVALS[rec.mastery] * DAY
        else:
            rec.wrong += 1
            rec.streak = 0
            rec.mastery = max(0, rec.mastery - 1)
            rec.next = now
        rec.last = now
        rec.last_pick = now
        db.add(rec)
        db.commit()
        db.refresh(rec)

        # 更新每日统计
        _update_daily_stats(db, now, is_correct)

        return rec.to_dict()


def _update_daily_stats(db, now: int, is_correct: bool):
    """每次答题后更新当日统计"""
    from datetime import datetime
    today = datetime.fromtimestamp(now).strftime("%Y-%m-%d")
    stat = db.query(DailyStats).filter(DailyStats.date == today, DailyStats.subject == "all").first()
    if not stat:
        stat = DailyStats(date=today, subject="all", total_answered=0, total_correct=0, accuracy=0.0)
    stat.total_answered += 1
    if is_correct:
        stat.total_correct += 1
    stat.accuracy = round(stat.total_correct / stat.total_answered * 100, 1)
    db.add(stat)
    db.commit()


@app.get("/api/get_record/{qid}")
def api_get_record(qid: str):
    with SessionLocal() as db:
        rec = db.query(Record).filter(Record.qid == qid).first()
        return rec.to_dict() if rec else None


@app.get("/api/all_records")
def api_all_records():
    with SessionLocal() as db:
        recs = db.query(Record).all()
        return [r.to_dict() for r in recs]


@app.get("/api/review_queue")
def api_review_queue(limit: int = 100, subject: str = None, qtype: str = None):
    with SessionLocal() as db:
        recs = db.query(Record).filter(Record.wrong > 0).all()
        if subject:
            recs = [r for r in recs if r.qid.startswith(subject + "_")]
        if qtype:
            recs = [r for r in recs if ("_" + qtype + "_") in r.qid]
        recs.sort(key=priority, reverse=True)
        return [r.qid for r in recs[:limit]]


@app.get("/api/due_count")
def api_due_count():
    with SessionLocal() as db:
        now = int(time.time())
        count = db.query(Record).filter(Record.wrong > 0, Record.next <= now).count()
        return {"count": count}


@app.get("/api/stats")
def api_stats():
    with SessionLocal() as db:
        recs = db.query(Record).all()
        total_ans = sum(r.correct + r.wrong for r in recs)
        total_c = sum(r.correct for r in recs)
        total_w = sum(r.wrong for r in recs)
        wrong_n = sum(1 for r in recs if r.wrong > 0)
        learned = len(set(r.qid for r in recs if r.correct + r.wrong > 0))
        now = int(time.time())
        due = sum(1 for r in recs if r.wrong > 0 and r.next <= now)
        acc = round(total_c / total_ans * 100) if total_ans > 0 else 0
        return {
            "total_answered": total_ans, "total_correct": total_c,
            "total_wrong": total_w, "wrong_count": wrong_n,
            "learned": learned, "due": due, "accuracy": acc,
        }


@app.get("/api/wrong_list")
def api_wrong_list(limit: int = 30):
    with SessionLocal() as db:
        recs = db.query(Record).filter(Record.wrong > 0).order_by(
            Record.wrong.desc()).limit(limit).all()
        return [r.to_dict() for r in recs]


@app.get("/api/clear_all")
def api_clear_all():
    with SessionLocal() as db:
        db.query(Record).delete()
        db.query(DailyStats).delete()
        db.commit()
        return {"ok": True}


# ═══════════════════════════════════════════════════════
#  API：模拟考试
# ═══════════════════════════════════════════════════════

class ExamResultIn(BaseModel):
    subject: str
    subject_name: str
    score: int
    pass_line: int
    passed: bool
    single_got: int = 0
    single_total: int = 0
    multi_got: int = 0
    multi_total: int = 0
    judge_got: int = 0
    judge_total: int = 0
    detail: str = ""


@app.post("/api/exam_result")
def api_save_exam_result(data: ExamResultIn):
    with SessionLocal() as db:
        rec = ExamResult(
            subject=data.subject, subject_name=data.subject_name,
            score=data.score, pass_line=data.pass_line,
            passed=1 if data.passed else 0,
            single_got=data.single_got, single_total=data.single_total,
            multi_got=data.multi_got, multi_total=data.multi_total,
            judge_got=data.judge_got, judge_total=data.judge_total,
            detail=data.detail, created_at=int(time.time()),
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec.to_dict()


@app.get("/api/exam_results")
def api_exam_results(subject: str = ""):
    with SessionLocal() as db:
        q = db.query(ExamResult)
        if subject:
            q = q.filter(ExamResult.subject == subject)
        recs = q.order_by(ExamResult.created_at.desc()).all()
        return [r.to_dict() for r in recs]


@app.delete("/api/exam_result/{exam_id}")
def api_delete_exam_result(exam_id: int):
    with SessionLocal() as db:
        rec = db.query(ExamResult).filter(ExamResult.id == exam_id).first()
        if rec:
            db.delete(rec)
            db.commit()
        return {"ok": True}


# ═══════════════════════════════════════════════════════
#  API：学科配置
# ═══════════════════════════════════════════════════════

class SubjectConfigIn(BaseModel):
    subject: str
    subject_name: str = ""
    exam_date: int = 0
    pass_line: int = 60


@app.get("/api/subject_configs")
def api_get_subject_configs():
    with SessionLocal() as db:
        recs = db.query(SubjectConfig).all()
        return [r.to_dict() for r in recs]


@app.post("/api/subject_configs")
def api_save_subject_config(data: SubjectConfigIn):
    with SessionLocal() as db:
        rec = db.query(SubjectConfig).filter(
            SubjectConfig.subject == data.subject).first()
        if not rec:
            rec = SubjectConfig(subject=data.subject)
        rec.subject_name = data.subject_name or data.subject
        rec.exam_date = data.exam_date
        rec.pass_line = data.pass_line
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec.to_dict()


@app.get("/api/subject_configs/{subject}")
def api_get_subject_config(subject: str):
    with SessionLocal() as db:
        rec = db.query(SubjectConfig).filter(
            SubjectConfig.subject == subject).first()
        return rec.to_dict() if rec else None


# ═══════════════════════════════════════════════════════
#  API：每日统计（趋势数据）
# ═══════════════════════════════════════════════════════

@app.get("/api/daily_stats")
def api_daily_stats(days: int = 14):
    """获取最近 N 天的答题统计"""
    from datetime import datetime, timedelta
    with SessionLocal() as db:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        stats = db.query(DailyStats).filter(
            DailyStats.date >= cutoff, DailyStats.subject == "all"
        ).order_by(DailyStats.date.asc()).all()
        return [s.to_dict() for s in stats]


# ═══════════════════════════════════════════════════════
#  API：复习建议 V1（保持向后兼容）
# ═══════════════════════════════════════════════════════

@app.get("/api/review_suggestion/{subject}")
def api_review_suggestion(subject: str):
    with SessionLocal() as db:
        recs = db.query(Record).filter(Record.qid.startswith(subject + "_")).all()
        config = db.query(SubjectConfig).filter(SubjectConfig.subject == subject).first()

    now = int(time.time())
    exam_date = config.exam_date if config else 0
    pass_line = config.pass_line if config else 60
    days_left = max(0, round((exam_date - now) / DAY)) if exam_date > 0 else -1

    total = len(recs)
    answered = sum(1 for r in recs if r.correct + r.wrong > 0)
    correct = sum(r.correct for r in recs)
    wrong = sum(r.wrong for r in recs)
    acc = round(correct / max(1, correct + wrong) * 100) if answered > 0 else 0

    single_recs = [r for r in recs if "_single_" in r.qid]
    multi_recs = [r for r in recs if "_multi_" in r.qid]
    judge_recs = [r for r in recs if "_judge_" in r.qid]

    def type_stats(rs):
        a = sum(1 for r in rs if r.correct + r.wrong > 0)
        c = sum(r.correct for r in rs)
        w = sum(r.wrong for r in rs)
        ac = round(c / max(1, c + w) * 100) if a > 0 else 0
        weak = sum(1 for r in rs if r.mastery == 0 and r.wrong > 0)
        return {"answered": a, "accuracy": ac, "weak": weak, "total": len(rs)}

    single_stat = type_stats(single_recs)
    multi_stat = type_stats(multi_recs)
    judge_stat = type_stats(judge_recs)

    weak_qids = [r.qid for r in recs if r.mastery == 0 and r.wrong > 0]
    weak_qids.sort(key=lambda q: next(
        (r.wrong for r in recs if r.qid == q), 0), reverse=True)

    suggestions = []
    if days_left < 0:
        phase = "no_exam"
        suggestions.append("未设置考试日期，建议先设置考试日期以获得更精准的复习建议")
        suggestions.append("建议每天保持 30-50 道题的练习量，保持手感")
    elif days_left > 14:
        phase = "long_term"
        suggestions.append(f"距离考试还有 {days_left} 天，属于长期备考阶段")
        suggestions.append("建议每天练习 50-80 道题，全面覆盖所有知识点")
        suggestions.append("优先完成所有题目至少一遍，建立知识框架")
        suggestions.append("多选题是拉分关键，建议多花时间练习")
    elif days_left > 7:
        phase = "mid_term"
        suggestions.append(f"距离考试还有 {days_left} 天，进入中期巩固阶段")
        suggestions.append("建议每天练习 40-60 道题，重点攻克错题")
        suggestions.append("使用「错题优先」模式，把所有掌握度0的题过一遍")
        suggestions.append("模拟考试每周做 1-2 次，检验复习效果")
    elif days_left > 3:
        phase = "short_term"
        suggestions.append(f"距离考试还有 {days_left} 天，进入冲刺阶段")
        suggestions.append("建议每天练习 30-50 道题，只看错题和薄弱点")
        suggestions.append("重点复习多选题和判断题的高频错题")
        suggestions.append("模拟考试每 2 天做一次，保持考试状态")
    elif days_left >= 1:
        phase = "final"
        suggestions.append(f"距离考试只剩 {days_left} 天，考前最后冲刺")
        suggestions.append("只看错题，不刷新题，确保做过错题不再错")
        suggestions.append("重点背记多选题的正确选项组合")
        suggestions.append("做一套模拟题热身，保持手感即可")
        suggestions.append("保证充足睡眠，比多刷几道题更重要")
    else:
        phase = "exam_day"
        suggestions.append("今天就是考试日！")
        suggestions.append("快速过一遍错题本，只看正确答案加深印象")
        suggestions.append("提前准备好考试用品，提前到达考场")
        suggestions.append("保持平常心，正常发挥一定能过！")

    priority_types = []
    if multi_stat["weak"] > 0:
        priority_types.append(f"多选题（{multi_stat['weak']}道顽固错题）")
    if judge_stat["weak"] > 0:
        priority_types.append(f"判断题（{judge_stat['weak']}道顽固错题）")
    if single_stat["weak"] > 0:
        priority_types.append(f"单选题（{single_stat['weak']}道顽固错题）")

    daily_target = 0
    if days_left < 0:
        daily_target = 50
    elif days_left > 14:
        daily_target = 60
    elif days_left > 7:
        daily_target = 50
    elif days_left > 3:
        daily_target = 40
    else:
        daily_target = max(20, len(weak_qids) // max(1, days_left))

    return {
        "subject": subject,
        "exam_date": exam_date,
        "days_left": days_left,
        "pass_line": pass_line,
        "phase": phase,
        "total_questions": total,
        "answered": answered,
        "accuracy": acc,
        "single_stat": single_stat,
        "multi_stat": multi_stat,
        "judge_stat": judge_stat,
        "weak_count": len(weak_qids),
        "weak_qids": weak_qids[:50],
        "priority_types": priority_types,
        "daily_target": daily_target,
        "suggestions": suggestions,
        "progress": round(answered / max(1, total) * 100) if total > 0 else 0,
    }


# ═══════════════════════════════════════════════════════
#  API：增强复习建议 V2（数据驱动 + 时间感知）
# ═══════════════════════════════════════════════════════

@app.get("/api/review_suggestion_v2/{subject}")
def api_review_suggestion_v2(subject: str):
    """增强版复习建议：结合答题趋势、薄弱环节、考试准备度"""
    v1 = api_review_suggestion(subject)
    with SessionLocal() as db:
        recs = db.query(Record).filter(Record.qid.startswith(subject + "_")).all()

    now = int(time.time())
    exam_date = v1["exam_date"]
    days_left = v1["days_left"]

    # ── 1. 趋势分析 ──
    from datetime import datetime, timedelta
    trend_data = _calc_trend(subject)
    trend = trend_data["trend"]
    trend_detail = trend_data["detail"]

    # ── 2. 薄弱环节分析 ──
    weak_areas = _analyze_weak_areas(recs)

    # ── 3. 考试准备度 ──
    readiness = _calc_readiness(v1, weak_areas, trend, days_left)

    # ── 4. 每日计划 ──
    daily_plan = _build_daily_plan(v1, weak_areas, days_left)

    # ── 5. 综合建议 ──
    suggestions = v1["suggestions"][:]  # 保留阶段建议
    # 追加数据驱动的个性化建议
    for wa in weak_areas[:3]:
        if wa["accuracy"] < 60:
            suggestions.append(
                f"{wa['topic']}准确率仅{wa['accuracy']}%，"
                f"建议每天专门练习{max(5, wa['count'] // max(1, days_left) if days_left > 0 else 10)}道{wa['topic']}"
            )
    weak_count = v1["weak_count"]
    if weak_count > 0 and days_left > 0:
        suggestions.append(
            f"有{weak_count}道顽固错题需要攻克，"
            f"使用「错题复习」模式，每天至少解决{min(weak_count, max(10, weak_count // max(1, days_left)))}道"
        )
    if readiness["score"] >= 80:
        suggestions.append("准备度良好，保持当前节奏即可，注意休息调整状态")
    elif readiness["score"] < 50:
        suggestions.append("准备度偏低，建议加大练习量，重点攻克薄弱题型")

    # ── 6. 历史趋势图数据 ──
    historical_trend = _get_historical_trend(subject, 14)

    return {
        **v1,
        "overall": {
            "progress": v1["progress"],
            "accuracy": v1["accuracy"],
            "trend": trend,
            "trend_detail": trend_detail,
        },
        "weak_areas": weak_areas,
        "daily_plan": daily_plan,
        "exam_readiness": readiness,
        "suggestions": suggestions,
        "historical_trend": historical_trend,
    }


def _calc_trend(subject: str) -> dict:
    """计算近期正确率趋势"""
    from datetime import datetime, timedelta
    with SessionLocal() as db:
        today = datetime.now()
        recent_cutoff = (today - timedelta(days=3)).strftime("%Y-%m-%d")
        earlier_cutoff = (today - timedelta(days=6)).strftime("%Y-%m-%d")
        mid_cutoff = (today - timedelta(days=3)).strftime("%Y-%m-%d")

        recent = db.query(DailyStats).filter(
            DailyStats.date >= recent_cutoff, DailyStats.subject == "all"
        ).all()
        earlier = db.query(DailyStats).filter(
            DailyStats.date >= earlier_cutoff,
            DailyStats.date < mid_cutoff,
            DailyStats.subject == "all"
        ).all()

    def avg_acc(stats):
        if not stats:
            return 0
        total_ans = sum(s.total_answered for s in stats)
        total_cor = sum(s.total_correct for s in stats)
        return round(total_cor / total_ans * 100, 1) if total_ans > 0 else 0

    recent_acc = avg_acc(recent)
    earlier_acc = avg_acc(earlier)

    if recent_acc == 0 and earlier_acc == 0:
        trend = "new"
        detail = "刚开始练习，尚无足够数据"
    elif recent_acc >= earlier_acc + 5:
        trend = "improving"
        detail = f"近3天正确率{recent_acc}%，较前期{earlier_acc}%明显提升"
    elif recent_acc <= earlier_acc - 5:
        trend = "declining"
        detail = f"近3天正确率{recent_acc}%，较前期{earlier_acc}%有所下降，注意复习质量"
    else:
        trend = "stable"
        detail = f"近3天正确率{recent_acc}%，与前期{earlier_acc}%基本持平"

    return {"trend": trend, "detail": detail, "recent_accuracy": recent_acc}


def _analyze_weak_areas(recs: list) -> list:
    """分析薄弱环节：按题型维度"""
    type_labels = {"single": "单选题", "multi": "多选题", "judge": "判断题"}
    weak_areas = []

    for qtype, label in type_labels.items():
        type_recs = [r for r in recs if f"_{qtype}_" in r.qid]
        answered = [r for r in type_recs if r.correct + r.wrong > 0]
        if not answered:
            continue
        correct = sum(r.correct for r in answered)
        wrong = sum(r.wrong for r in answered)
        total_ans = correct + wrong
        acc = round(correct / total_ans * 100) if total_ans > 0 else 0
        weak_count = sum(1 for r in type_recs if r.mastery == 0 and r.wrong > 0)

        priority = "high" if acc < 60 else "medium" if acc < 75 else "low"
        weak_areas.append({
            "topic": label, "type": qtype,
            "accuracy": acc, "count": weak_count,
            "total_answered": len(answered), "total": len(type_recs),
            "priority": priority,
        })

    weak_areas.sort(key=lambda x: x["accuracy"])
    return weak_areas


def _calc_readiness(v1: dict, weak_areas: list, trend: str, days_left: int) -> dict:
    """计算考试准备度 0-100"""
    score = 50  # 基础分

    # 进度加分（最多+20）
    score += min(20, v1["progress"] * 0.2)

    # 正确率加减（最多±20）
    acc_offset = (v1["accuracy"] - 60) * 0.5
    score += max(-20, min(20, acc_offset))

    # 薄弱项扣分（最多-15）
    high_priority = [w for w in weak_areas if w["priority"] == "high"]
    score -= len(high_priority) * 5

    # 趋势加减（最多±10）
    if trend == "improving":
        score += 10
    elif trend == "declining":
        score -= 10

    # 时间压力（如果设了考试日期）
    if days_left > 14:
        score += 5  # 时间充裕
    elif days_left < 0:
        pass  # 无考试日期，不调整
    elif days_left < 3:
        score -= 5  # 时间紧迫

    score = max(0, min(100, round(score)))

    if score >= 80:
        level = "充分准备"
    elif score >= 65:
        level = "基本就绪"
    elif score >= 50:
        level = "需要加强"
    else:
        level = "差距较大"

    # 准备度因素分析
    factors = []
    if v1["progress"] < 50:
        factors.append(f"仅完成{v1['progress']}%题目，进度需要加快")
    else:
        factors.append(f"已完成{v1['progress']}%题目，进度良好")
    if v1["accuracy"] < 65:
        factors.append(f"正确率{v1['accuracy']}%偏低，注意答题质量")
    else:
        factors.append(f"正确率{v1['accuracy']}%，表现不错")
    if high_priority:
        factors.append(f"有{len(high_priority)}个薄弱题型需要重点攻克")
    if days_left >= 0:
        factors.append(f"距考试还有{days_left}天，{'时间充裕' if days_left > 7 else '需要抓紧'}")
    factors.append(f"趋势：{'上升中 ▲' if trend == 'improving' else '下降中 ▼' if trend == 'declining' else '保持稳定 ▶' if trend == 'stable' else '数据不足'}")

    return {"score": score, "level": level, "factors": factors}


def _build_daily_plan(v1: dict, weak_areas: list, days_left: int) -> dict:
    """构建每日练习计划"""
    daily_target = v1["daily_target"]

    # 计算各题型配额
    single_pct = v1["single_stat"]["total"] / max(1, v1["total_questions"])
    multi_pct = v1["multi_stat"]["total"] / max(1, v1["total_questions"])
    judge_pct = v1["judge_stat"]["total"] / max(1, v1["total_questions"])

    # 薄弱题型加权（多分配一些）
    for wa in weak_areas:
        if wa["priority"] == "high":
            if wa["type"] == "single":
                single_pct *= 1.3
            elif wa["type"] == "multi":
                multi_pct *= 1.5
            elif wa["type"] == "judge":
                judge_pct *= 1.3

    # 归一化
    total_pct = single_pct + multi_pct + judge_pct
    single_pct /= total_pct
    multi_pct /= total_pct
    judge_pct /= total_pct

    single_target = max(5, round(daily_target * single_pct))
    multi_target = max(3, round(daily_target * multi_pct))
    judge_target = max(3, round(daily_target * judge_pct))

    # 重点攻克领域
    focus_areas = []
    for wa in weak_areas:
        if wa["priority"] in ("high", "medium"):
            focus_areas.append(wa["topic"])

    return {
        "target_questions": daily_target,
        "breakdown": {
            "single": single_target,
            "multi": multi_target,
            "judge": judge_target,
        },
        "focus_areas": focus_areas[:3],
    }


def _get_historical_trend(subject: str, days: int = 14) -> list:
    """获取历史正确率趋势数据"""
    from datetime import datetime, timedelta
    with SessionLocal() as db:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        stats = db.query(DailyStats).filter(
            DailyStats.date >= cutoff, DailyStats.subject == "all"
        ).order_by(DailyStats.date.asc()).all()

    result = []
    for s in stats:
        result.append({
            "date": s.date[-5:],  # "07-25"
            "accuracy": s.accuracy,
            "answered": s.total_answered,
        })
    return result


# ═══════════════════════════════════════════════════════
#  API：复习建议总览（全部科目）
# ═══════════════════════════════════════════════════════

@app.get("/api/review_suggestion_all")
def api_review_suggestion_all():
    with SessionLocal() as db:
        recs = db.query(Record).all()
        configs = db.query(SubjectConfig).all()
        config_map = {c.subject: c for c in configs}

    now = int(time.time())
    total = len(recs)
    answered = sum(1 for r in recs if r.correct + r.wrong > 0)
    correct = sum(r.correct for r in recs)
    acc = round(correct / max(1, correct + sum(r.wrong for r in recs)) * 100) if answered > 0 else 0
    due = sum(1 for r in recs if r.wrong > 0 and r.next <= now)
    wrong_count = sum(1 for r in recs if r.wrong > 0)

    exam_dates = [c.exam_date for c in configs if c.exam_date > 0]
    nearest_exam = min(exam_dates) if exam_dates else 0
    days_left = max(0, round((nearest_exam - now) / DAY)) if nearest_exam > 0 else -1

    suggestions = []
    if days_left < 0:
        phase = "no_exam"
        suggestions.append("未设置考试日期，可在设置中配置各科目考试时间")
        suggestions.append(f"当前共 {total} 道题，已完成 {answered} 道，正确率 {acc}%")
        suggestions.append(f"待复习错题 {wrong_count} 道，建议每天保持练习")
    elif days_left > 14:
        phase = "long_term"
        suggestions.append(f"距离最近的考试还有 {days_left} 天，长期备考阶段")
        suggestions.append(f"总进度：{answered}/{total} 题（{round(answered/max(1,total)*100)}%），正确率 {acc}%")
        suggestions.append("建议按科目逐个突破，每天每科 20-30 题")
        suggestions.append("重点关注多选题，分值高容易拉分")
    elif days_left > 7:
        phase = "mid_term"
        suggestions.append(f"距离最近的考试还有 {days_left} 天，中期巩固阶段")
        suggestions.append(f"待复习错题 {due} 道，优先攻克错题")
        suggestions.append("建议每天练习 40-60 题，使用错题复习模式")
        suggestions.append("每科至少做 1 次模拟考试，检验复习效果")
    elif days_left > 3:
        phase = "short_term"
        suggestions.append(f"距离最近的考试还有 {days_left} 天，冲刺阶段")
        suggestions.append("只刷错题，不刷新题，确保错题不再错")
        suggestions.append("重点复习多选题和判断题的高频考点")
        suggestions.append("每 2 天做一套模拟卷，保持考试状态")
    elif days_left >= 1:
        phase = "final"
        suggestions.append(f"距离最近的考试只剩 {days_left} 天，最后冲刺")
        suggestions.append("只看错题的正确答案，加深印象")
        suggestions.append("做 1-2 套模拟题热身，保持手感")
        suggestions.append("保证充足睡眠，调整好状态")
    else:
        phase = "exam_day"
        suggestions.append("今天是考试日！加油！")
        suggestions.append("快速浏览错题本，只看正确选项")
        suggestions.append("提前准备好证件和考试用品")
        suggestions.append("保持平常心，正常发挥就好")

    # 趋势数据
    trend_data = _calc_trend("all")

    return {
        "phase": phase, "days_left": days_left,
        "total_questions": total, "answered": answered, "accuracy": acc,
        "wrong_count": wrong_count, "due": due,
        "progress": round(answered / max(1, total) * 100) if total > 0 else 0,
        "suggestions": suggestions,
        "trend": trend_data["trend"],
        "trend_detail": trend_data["detail"],
    }


# ═══════════════════════════════════════════════════════
#  API：上传 & 解析
# ═══════════════════════════════════════════════════════

@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...), auto_parse: str = "true"):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".docx", ".pdf", ".zip", ".txt"]:
        raise HTTPException(status_code=400,
                           detail=f"不支持的文件格式: {ext}。支持 .docx, .pdf, .zip, .txt")

    # 清理旧上传文件（保留本次的）
    if os.path.exists(UPLOAD_DIR):
        import shutil
        for old in os.listdir(UPLOAD_DIR):
            old_path = os.path.join(UPLOAD_DIR, old)
            try:
                if os.path.isfile(old_path):
                    os.remove(old_path)
                elif os.path.isdir(old_path):
                    shutil.rmtree(old_path)
            except Exception:
                pass

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    result = {"ok": True, "filename": file.filename, "size": len(content)}

    # 自动解析
    if auto_parse != "false":
        try:
            parse_result = _do_parse()
            result["parsed"] = True
            result["parse_result"] = parse_result
        except Exception as e:
            import traceback
            result["parsed"] = False
            result["parse_error"] = str(e)
            result["parse_traceback"] = traceback.format_exc()

    return result


def _do_parse():
    """执行解析并返回结果"""
    from question_parser import parse_folder, generate_questions_js
    bank = parse_folder(UPLOAD_DIR)
    total = sum(len(s["questions"]) for s in bank["subjects"])
    generate_questions_js(bank, QUESTIONS_JS)

    with SessionLocal() as db:
        for s in bank["subjects"]:
            rec = db.query(SubjectConfig).filter(
                SubjectConfig.subject == s["id"]).first()
            if not rec:
                rec = SubjectConfig(subject=s["id"], subject_name=s["name"],
                                    exam_date=0, pass_line=60)
                db.add(rec)
        db.commit()

    return {
        "ok": True,
        "subject_count": len(bank["subjects"]),
        "total_questions": total,
        "subjects": [{"id": s["id"], "name": s["name"],
                      "count": len(s["questions"])} for s in bank["subjects"]],
    }


@app.post("/api/parse")
def api_parse():
    try:
        result = _do_parse()
        return result
    except Exception as e:
        import traceback
        return {"ok": False, "error": str(e), "traceback": traceback.format_exc()}


@app.get("/api/uploads")
def api_uploads():
    files = []
    if os.path.exists(UPLOAD_DIR):
        for name in sorted(os.listdir(UPLOAD_DIR)):
            path = os.path.join(UPLOAD_DIR, name)
            if os.path.isfile(path):
                size = os.path.getsize(path)
                files.append({"name": name, "size": size})
    return files


@app.delete("/api/uploads/{filename}")
def api_delete_upload(filename: str):
    path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        return {"ok": True}
    raise HTTPException(status_code=404, detail="File not found")


# ═══════════════════════════════════════════════════════
#  API：题库信息
# ═══════════════════════════════════════════════════════

@app.get("/api/bank_info")
def api_bank_info():
    if not os.path.exists(QUESTIONS_JS):
        return {"has_bank": False}
    try:
        with open(QUESTIONS_JS, "r", encoding="utf-8") as f:
            content = f.read()
        eq_idx = content.index("=")
        json_str = content[eq_idx + 1:].strip().rstrip(";")
        data = json.loads(json_str)
        subjects = []
        total = 0
        for s in data.get("subjects", []):
            cnt = len(s.get("questions", []))
            total += cnt
            qtypes = {}
            for q in s.get("questions", []):
                t = q.get("type", "unknown")
                qtypes[t] = qtypes.get(t, 0) + 1
            subjects.append({
                "id": s["id"], "name": s["name"],
                "count": cnt, "types": qtypes,
            })
        return {
            "has_bank": True, "subject_count": len(subjects),
            "total": total, "subjects": subjects,
        }
    except Exception as e:
        return {"has_bank": False, "error": str(e)}


@app.delete("/api/subject/{subject_id}")
def api_delete_subject(subject_id: str):
    """删除指定学科及其所有题目（支持 ID 或名称匹配）"""
    if not os.path.exists(QUESTIONS_JS):
        raise HTTPException(status_code=404, detail="题库文件不存在，请先上传题库")
    try:
        with open(QUESTIONS_JS, "r", encoding="utf-8") as f:
            content = f.read()
        eq_idx = content.index("=")
        json_str = content[eq_idx + 1:].strip().rstrip(";")
        data = json.loads(json_str)

        subjects = data.get("subjects", [])
        # 尝试多种匹配方式：ID 精确匹配 → 名称精确匹配 → 名称包含匹配 → ID 包含匹配
        target = None
        target = next((s for s in subjects if s["id"] == subject_id), None)
        if not target:
            target = next((s for s in subjects if s.get("name") == subject_id), None)
        if not target:
            target = next((s for s in subjects if subject_id in s.get("name", "")), None)
        if not target:
            target = next((s for s in subjects if subject_id in s["id"]), None)

        if not target:
            available = [f'{s["id"]}({s.get("name", "")})' for s in subjects]
            raise HTTPException(
                status_code=404,
                detail=f"未找到学科「{subject_id}」。当前题库中的学科: {', '.join(available) if available else '(空)'}"
            )

        # 收集要删除的题目 ID
        actual_id = target["id"]
        removed_qids = [q["id"] for q in target.get("questions", [])]
        removed_name = target.get("name", subject_id)
        removed_count = len(removed_qids)

        # 从题库中移除
        data["subjects"] = [s for s in subjects if s["id"] != actual_id]
        with open(QUESTIONS_JS, "w", encoding="utf-8") as f:
            f.write("window.QUESTION_BANK = " + json.dumps(data, ensure_ascii=False) + ";\n")

        # 清理上传文件夹中对应的源文件
        import shutil
        for fname in os.listdir(UPLOAD_DIR):
            fpath = os.path.join(UPLOAD_DIR, fname)
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
                elif os.path.isdir(fpath):
                    shutil.rmtree(fpath)
            except Exception:
                pass

        # 清理相关答题记录、考试记录、学科配置
        with SessionLocal() as db:
            for qid in removed_qids:
                db.query(Record).filter(Record.qid == qid).delete()
            db.query(Record).filter(Record.qid.like(actual_id + "_%")).delete()
            db.query(ExamResult).filter(ExamResult.subject == actual_id).delete()
            db.query(SubjectConfig).filter(SubjectConfig.subject == actual_id).delete()
            db.commit()

        return {
            "ok": True,
            "subject_id": actual_id,
            "subject_name": removed_name,
            "removed_questions": removed_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/bank/clear")
def api_clear_bank():
    """清空全部题库及所有关联数据"""
    if os.path.exists(QUESTIONS_JS):
        with open(QUESTIONS_JS, "w", encoding="utf-8") as f:
            f.write('window.QUESTION_BANK = {"subjects": []};\n')
    # 清理上传文件
    import shutil
    if os.path.exists(UPLOAD_DIR):
        for fname in os.listdir(UPLOAD_DIR):
            fpath = os.path.join(UPLOAD_DIR, fname)
            try:
                if os.path.isfile(fpath): os.remove(fpath)
                elif os.path.isdir(fpath): shutil.rmtree(fpath)
            except Exception: pass
    # 清理数据库
    with SessionLocal() as db:
        db.query(Record).delete()
        db.query(ExamResult).delete()
        db.query(SubjectConfig).delete()
        db.query(DailyStats).delete()
        db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════
#  静态文件 & 路由
# ═══════════════════════════════════════════════════════

app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")


@app.get("/questions.js")
def serve_questions():
    if os.path.exists(QUESTIONS_JS):
        return FileResponse(QUESTIONS_JS)
    default_qjs = os.path.join(BASE_DIR, "questions.js")
    if os.path.exists(default_qjs):
        return FileResponse(default_qjs)
    return JSONResponse({"error": "no questions"}, status_code=404)


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


# ═══════════════════════════════════════════════════════
#  启动
# ═══════════════════════════════════════════════════════

def open_browser():
    time.sleep(1.5)
    try:
        webbrowser.open(f"http://localhost:{FRONTEND_PORT}")
    except Exception:
        pass


def _get_local_ip():
    """获取本机局域网 IP"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def _show_error(message):
    """显示错误消息并写入日志文件"""
    try:
        log_dir = _get_data_dir()
        log_file = os.path.join(log_dir, "error.log")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(message)
    except Exception:
        pass
    print("ERROR:", message, file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("QuizMasterPro V2 Error", message)
        root.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        import uvicorn
        if os.environ.get("NO_AUTO_OPEN") != "1":
            threading.Thread(target=open_browser, daemon=True).start()
        local_ip = _get_local_ip()
        print(f"")
        print(f"  QuizMasterPro V2")
        print(f"  本机: http://localhost:{FRONTEND_PORT}")
        if local_ip:
            print(f"  局域网: http://{local_ip}:{FRONTEND_PORT}")
        print(f"  数据: {_get_data_dir()}")
        print(f"")
        uvicorn.run(app, host="0.0.0.0", port=FRONTEND_PORT)
    except Exception as e:
        import traceback
        err_msg = f"启动失败:\n{str(e)}\n\n{traceback.format_exc()}"
        _show_error(err_msg)
        # 保持控制台可见
        print("\n" + err_msg)
        print("\n按 Enter 键退出...")
        try:
            input()
        except Exception:
            pass
        sys.exit(1)
