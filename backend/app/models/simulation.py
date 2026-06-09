import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Simulation(Base):
    __tablename__ = "simulations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    num_simulations: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    config: Mapped[str] = mapped_column(Text, nullable=True)

    results: Mapped[list["SimulationResult"]] = relationship(
        "SimulationResult", back_populates="simulation", cascade="all, delete-orphan"
    )


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    group_name: Mapped[str] = mapped_column(String(10), nullable=True)
    group_position: Mapped[int] = mapped_column(Integer, nullable=True)
    reached_round_of_32: Mapped[int] = mapped_column(Integer, default=0)
    reached_round_of_16: Mapped[int] = mapped_column(Integer, default=0)
    reached_quarter_final: Mapped[int] = mapped_column(Integer, default=0)
    reached_semi_final: Mapped[int] = mapped_column(Integer, default=0)
    reached_final: Mapped[int] = mapped_column(Integer, default=0)
    won_tournament: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[float] = mapped_column(Float, default=0.0)

    simulation: Mapped["Simulation"] = relationship("Simulation", back_populates="results")
    team: Mapped["Team"] = relationship("Team", back_populates="simulation_results")
