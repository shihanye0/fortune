# -*- coding: utf-8 -*-
"""事件验证接口"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.users import get_current_user
from app.models.daily_fortune import DailyFortune
from app.models.divination_record import DivinationRecord
from app.models.prediction_outcome import PredictionOutcome
from app.models.user import User


router = APIRouter(prefix="/prediction-outcomes", tags=["事件验证"])


# --- Schema ---

class PredictionOutcomeRequest(BaseModel):
    source_type: str = Field(..., pattern=r"^(fortune|divination)$", description="来源类型")
    source_id: int = Field(..., ge=1, description="来源记录ID")
    outcome_text: str | None = Field(None, description="事件结果描述")
    verified: bool | None = Field(None, description="事件是否确实发生")


# --- 路由 ---

@router.post("")
def create_prediction_outcome(
    req: PredictionOutcomeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交事件验证"""
    # 验证来源记录是否存在且属于当前用户
    if req.source_type == "fortune":
        source = (
            db.query(DailyFortune)
            .filter(
                DailyFortune.id == req.source_id,
                DailyFortune.user_id == current_user.id,
            )
            .first()
        )
        if not source:
            raise HTTPException(status_code=404, detail="运势记录不存在")
    elif req.source_type == "divination":
        source = (
            db.query(DivinationRecord)
            .filter(
                DivinationRecord.id == req.source_id,
                DivinationRecord.user_id == current_user.id,
            )
            .first()
        )
        if not source:
            raise HTTPException(status_code=404, detail="占卜记录不存在")

        # 更新占卜记录的 outcome_verified 字段
        source.outcome_verified = req.verified
        db.commit()

    # 创建预测结果验证记录
    outcome = PredictionOutcome(
        user_id=current_user.id,
        source_type=req.source_type,
        source_id=req.source_id,
        outcome_text=req.outcome_text,
        verified=req.verified,
        verified_at=datetime.now(timezone.utc) if req.verified is not None else None,
    )
    db.add(outcome)
    db.commit()
    db.refresh(outcome)

    return {
        "success": True,
        "data": {
            "id": outcome.id,
            "source_type": outcome.source_type,
            "source_id": outcome.source_id,
            "outcome_text": outcome.outcome_text,
            "verified": outcome.verified,
            "verified_at": outcome.verified_at.isoformat() if outcome.verified_at else None,
            "created_at": outcome.created_at.isoformat() if outcome.created_at else None,
        },
    }
