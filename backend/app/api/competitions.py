from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.competition import Competition
from app.schemas.competition import CompetitionResponse

router = APIRouter(prefix="/competitions", tags=["Competitions"])


@router.get("/current", response_model=CompetitionResponse)
def get_current_competition(db: Session = Depends(get_db)):
    competition = db.query(Competition).order_by(Competition.start_date.desc()).first()
    if not competition:
        raise HTTPException(status_code=404, detail="No competition found")
    return competition
