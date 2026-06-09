import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api import analysis, calibration, groups, matches, predictions, rankings, simulations, teams
from app.core.config import get_settings
from app.db.session import engine, Base

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper()))

app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    description="Professional World Cup 2026 Tournament Forecasting Engine — "
    "simulate match outcomes, group stages, and entire tournaments with Monte Carlo methods.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(teams.router, prefix=settings.api_prefix)
app.include_router(matches.router, prefix=settings.api_prefix)
app.include_router(groups.router, prefix=settings.api_prefix)
app.include_router(predictions.router, prefix=settings.api_prefix)
app.include_router(rankings.router, prefix=settings.api_prefix)
app.include_router(simulations.router, prefix=settings.api_prefix)
app.include_router(calibration.router, prefix=settings.api_prefix)
app.include_router(analysis.router, prefix=settings.api_prefix)


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "project": settings.project_name, "version": settings.project_version}
