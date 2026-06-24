import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    home_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    away_team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    group_name: Mapped[str] = mapped_column(String(10), nullable=True)
    home_goals: Mapped[int] = mapped_column(Integer, nullable=True)
    away_goals: Mapped[int] = mapped_column(Integer, nullable=True)
    home_xg: Mapped[float] = mapped_column(Float, nullable=True)
    away_xg: Mapped[float] = mapped_column(Float, nullable=True)
    is_neutral_venue: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")

    competition: Mapped["Competition"] = relationship("Competition", back_populates="matches")
    home_team: Mapped["Team"] = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team: Mapped["Team"] = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")

    @property
    def home_team_name(self) -> str | None:
        return self.home_team.name if self.home_team else None

    @property
    def away_team_name(self) -> str | None:
        return self.away_team.name if self.away_team else None
