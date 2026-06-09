import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class FifaRanking(Base):
    __tablename__ = "fifa_rankings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ranking_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_rank: Mapped[int] = mapped_column(Integer, nullable=True)
    total_points: Mapped[float] = mapped_column(Float, nullable=False)
    confederation: Mapped[str] = mapped_column(String(100), nullable=True)

    team: Mapped["Team"] = relationship("Team", back_populates="fifa_rankings")
