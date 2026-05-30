import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from db.database import get_db
from db.models import Receipt

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary", summary="Spending totals by category (last N days)")
def spending_summary(days: int = 30, db: Session = Depends(get_db)):
    since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    rows = (
        db.query(Receipt.category, func.sum(Receipt.total), func.count(Receipt.id))
        .filter(Receipt.created_at >= since)
        .group_by(Receipt.category)
        .all()
    )
    categories = {
        (cat or "other"): {"total": round(float(tot), 2), "count": int(cnt)}
        for cat, tot, cnt in rows
    }
    return {
        "period_days": days,
        "grand_total": round(sum(v["total"] for v in categories.values()), 2),
        "by_category": categories,
    }


@router.get("/weekly", summary="Daily spending totals for the last 7 days")
def weekly_breakdown(db: Session = Depends(get_db)):
    since = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    rows = (
        db.query(
            func.date_trunc("day", Receipt.created_at).label("day"),
            func.sum(Receipt.total),
            func.count(Receipt.id),
        )
        .filter(Receipt.created_at >= since)
        .group_by("day")
        .order_by("day")
        .all()
    )
    return [
        {"date": str(day.date()), "total": round(float(tot), 2), "count": int(cnt)}
        for day, tot, cnt in rows
    ]


@router.get("/by-category", summary="All-time receipt count and total per category")
def by_category(db: Session = Depends(get_db)):
    rows = (
        db.query(Receipt.category, func.sum(Receipt.total), func.count(Receipt.id))
        .group_by(Receipt.category)
        .order_by(func.sum(Receipt.total).desc())
        .all()
    )
    return [
        {"category": cat or "other", "total": round(float(tot), 2), "count": int(cnt)}
        for cat, tot, cnt in rows
    ]
