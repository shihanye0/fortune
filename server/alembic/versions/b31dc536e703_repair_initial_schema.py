"""repair missing schema from the empty initial revision

Revision ID: b31dc536e703
Revises: 6f442fb65ec6
Create Date: 2026-09-18 15:30:00.000000

The historical initial revision was stamped but contained no DDL.  Some
existing installations therefore already have tables while a fresh database
does not.  `create_all(checkfirst=True)` repairs the latter without touching
the former.
"""

from alembic import op

from app.models.base import Base
from app.models.bazi_profile import BaziProfile  # noqa: F401
from app.models.daily_fortune import DailyFortune  # noqa: F401
from app.models.divination_record import DivinationRecord  # noqa: F401
from app.models.prediction_outcome import PredictionOutcome  # noqa: F401
from app.models.probability_event_feedback import ProbabilityEventFeedback  # noqa: F401
from app.models.user import User  # noqa: F401


# revision identifiers, used by Alembic.
revision = "b31dc536e703"
down_revision = "6f442fb65ec6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """只补建本修复迁移当时的表，不能吞掉后续正式迁移。"""
    Base.metadata.create_all(
        bind=op.get_bind(),
        tables=[
            User.__table__,
            BaziProfile.__table__,
            DailyFortune.__table__,
            DivinationRecord.__table__,
            PredictionOutcome.__table__,
            ProbabilityEventFeedback.__table__,
        ],
        checkfirst=True,
    )


def downgrade() -> None:
    """Keep tables intact: they may have existed before this repair migration."""
    # This repair is intentionally non-destructive.
    pass
