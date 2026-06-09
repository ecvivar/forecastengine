import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    fifa_code: Mapped[str] = mapped_column(String(3), nullable=True, unique=True, index=True)
    flag_url: Mapped[str] = mapped_column(String(512), nullable=True)
    continent: Mapped[str] = mapped_column(String(100), nullable=True)
    founded_year: Mapped[int] = mapped_column(Integer, nullable=True)
    is_national_team: Mapped[bool] = mapped_column(Boolean, default=True)

    players: Mapped[list["Player"]] = relationship("Player", back_populates="team")
    elo_ratings: Mapped[list["EloRating"]] = relationship("EloRating", back_populates="team")
    fifa_rankings: Mapped[list["FifaRanking"]] = relationship("FifaRanking", back_populates="team")
    xg_metrics: Mapped[list["XGMetrics"]] = relationship("XGMetrics", back_populates="team")
    home_matches: Mapped[list["Match"]] = relationship(
        "Match", foreign_keys="Match.home_team_id", back_populates="home_team"
    )
    away_matches: Mapped[list["Match"]] = relationship(
        "Match", foreign_keys="Match.away_team_id", back_populates="away_team"
    )
    group_standings: Mapped[list["GroupStanding"]] = relationship(
        "GroupStanding", back_populates="team"
    )
    simulation_results: Mapped[list["SimulationResult"]] = relationship(
        "SimulationResult", back_populates="team"
    )
