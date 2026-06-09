import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.team import Team
from app.schemas.team import TeamCreate, TeamUpdate


class TeamService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 20) -> list[Team]:
        return self.db.query(Team).offset(skip).limit(limit).all()

    def get_by_id(self, team_id: uuid.UUID) -> Team | None:
        return self.db.query(Team).filter(Team.id == team_id).first()

    def get_by_fifa_code(self, code: str) -> Team | None:
        return self.db.query(Team).filter(Team.fifa_code == code).first()

    def create(self, data: TeamCreate) -> Team:
        team = Team(**data.model_dump())
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def update(self, team_id: uuid.UUID, data: TeamUpdate) -> Team | None:
        team = self.get_by_id(team_id)
        if not team:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(team, key, value)
        self.db.commit()
        self.db.refresh(team)
        return team

    def delete(self, team_id: uuid.UUID) -> bool:
        team = self.get_by_id(team_id)
        if not team:
            return False
        self.db.delete(team)
        self.db.commit()
        return True

    def count(self) -> int:
        return self.db.query(Team).count()
