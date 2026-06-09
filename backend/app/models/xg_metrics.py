import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class XGMetrics(Base):
    __tablename__ = "xg_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    xg_for: Mapped[float] = mapped_column(Float, nullable=False)
    xg_against: Mapped[float] = mapped_column(Float, nullable=False)
    xg_diff: Mapped[float] = mapped_column(Float, nullable=True)
    non_penalty_xg: Mapped[float] = mapped_column(Float, nullable=True)
    shots_on_target: Mapped[int] = mapped_column(Integer, nullable=True)
    matches_sampled: Mapped[int] = mapped_column(Integer, default=1)

    team: Mapped["Team"] = relationship("Team", back_populates="xg_metrics")
