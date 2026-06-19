from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.cache_decorator import cached
from app.core.dependencies import get_db
from app.models.group import Group
from app.models.group_standing import GroupStanding
from app.schemas.group import GroupDetail, GroupStandingResponse

router = APIRouter(prefix="/groups", tags=["Groups"])


def _standing_response(standing: GroupStanding) -> GroupStandingResponse:
    return GroupStandingResponse(
        id=standing.id,
        group_id=standing.group_id,
        team_id=standing.team_id,
        team_name=standing.team.name if standing.team else "Unknown",
        position=standing.position,
        played=standing.played,
        won=standing.won,
        drawn=standing.drawn,
        lost=standing.lost,
        goals_for=standing.goals_for,
        goals_against=standing.goals_against,
        goal_difference=standing.goal_difference,
        points=standing.points,
        xg_for=standing.xg_for,
        xg_against=standing.xg_against,
        qualified=standing.qualified,
    )


def _group_detail(group: Group) -> GroupDetail:
    standings = [
        _standing_response(standing)
        for standing in sorted(group.standings, key=lambda x: x.position)
    ]
    return GroupDetail(
        id=group.id,
        competition_id=group.competition_id,
        name=group.name,
        stage=group.stage,
        standings=standings,
    )


@router.get("", response_model=list[GroupDetail])
def list_groups(db: Session = Depends(get_db)):
    groups = (
        db.query(Group)
        .options(joinedload(Group.standings).joinedload(GroupStanding.team))
        .order_by(Group.name)
        .all()
    )
    return [_group_detail(group) for group in groups]


@router.get("/{group_name}", response_model=GroupDetail)
@cached("groups:detail")
def get_group(group_name: str, db: Session = Depends(get_db)):
    group = (
        db.query(Group)
        .options(joinedload(Group.standings).joinedload(GroupStanding.team))
        .filter(Group.name == group_name.upper())
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return _group_detail(group)
