import uuid
from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    season: Mapped[str] = mapped_column(String(50), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    competition_type: Mapped[str] = mapped_column(
        String(50), default="world_cup"
    )
    format: Mapped[str] = mapped_column(String(50), default="group_plus_knockout")

    groups: Mapped[list["Group"]] = relationship("Group", back_populates="competition")
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="competition")
