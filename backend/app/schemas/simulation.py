import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SimulationCreate(BaseModel):
    competition_id: uuid.UUID
    name: str | None = None
    num_simulations: int = 10_000
    config: dict | None = None


class SimulationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    competition_id: uuid.UUID
    name: str | None = None
    num_simulations: int
    status: str
    created_at: datetime
    completed_at: datetime | None = None


class SimulationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: uuid.UUID
    group_name: str | None = None
    group_position: int | None = None
    reached_round_of_32: int = 0
    reached_round_of_16: int
    reached_quarter_final: int
    reached_semi_final: int
    reached_final: int
    won_tournament: int
    points: float

    @property
    def team_name(self) -> str:
        return ""

    @property
    def win_probability(self) -> float:
        return self.won_tournament / 100.0 if self.won_tournament > 0 else 0.0


class SimulationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    competition_id: uuid.UUID
    name: str | None = None
    num_simulations: int
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    results: list[SimulationResultResponse] = []


class SimulationDetail(SimulationResponse):
    results: list[SimulationResultResponse]
