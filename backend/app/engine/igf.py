"""
Global Strength Index (IGF) Engine.

Computes a composite strength score (0-100) per team using configurable weights.
Factors: Elo Ajustado (25%), Forma Reciente (20%), xG/xGA (20%),
         Fortaleza Rivales (10%), Experiencia Mundialista (10%),
         Calidad Plantel (10%), Historial Reciente Torneos (5%).
"""

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class IGFConfig:
    elo_weight: float = 0.25
    recent_form_weight: float = 0.20
    xg_weight: float = 0.12
    xga_weight: float = 0.08
    opponent_strength_weight: float = 0.10
    world_cup_experience_weight: float = 0.10
    squad_quality_weight: float = 0.10
    tournament_history_weight: float = 0.05

    @classmethod
    def from_settings(cls) -> "IGFConfig":
        return cls(
            elo_weight=getattr(settings, 'igf_elo_weight', 0.25),
            recent_form_weight=getattr(settings, 'igf_recent_form_weight', 0.20),
            xg_weight=getattr(settings, 'igf_xg_weight', 0.12),
            xga_weight=getattr(settings, 'igf_xga_weight', 0.08),
            opponent_strength_weight=getattr(settings, 'igf_opponent_strength_weight', 0.10),
            world_cup_experience_weight=getattr(settings, 'igf_world_cup_experience_weight', 0.10),
            squad_quality_weight=getattr(settings, 'igf_squad_quality_weight', 0.10),
            tournament_history_weight=getattr(settings, 'igf_tournament_history_weight', 0.05),
        )


class IGFEngine:
    """Computes the Global Strength Index (0-100) for all teams."""

    def __init__(self, config: IGFConfig | None = None):
        self.config = config or IGFConfig.from_settings()

    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        """Compute IGF scores (0-100) from a DataFrame with all factor columns."""
        required = ["elo_score", "xg_for", "xg_against", "fifa_rank"]
        missing = [c for c in required if c not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df = data.copy()

        df["norm_elo"] = self._normalize(df["elo_score"], higher_is_better=True)
        df["norm_xg"] = self._normalize(df["xg_for"], higher_is_better=True)
        df["norm_xga"] = self._normalize(df["xg_against"], higher_is_better=False)
        df["norm_rank"] = self._normalize(df["fifa_rank"], higher_is_better=False)

        if "recent_form" in df.columns:
            df["norm_form"] = self._normalize(df["recent_form"], higher_is_better=True)
        else:
            df["norm_form"] = 0.5

        if "wc_experience" in df.columns:
            df["norm_wc_exp"] = self._normalize(df["wc_experience"], higher_is_better=True)
        else:
            df["norm_wc_exp"] = 0.5

        if "squad_value" in df.columns:
            df["norm_squad"] = self._normalize(df["squad_value"], higher_is_better=True)
        else:
            df["norm_squad"] = 0.5

        if "opponent_strength" in df.columns:
            df["norm_opp"] = self._normalize(df["opponent_strength"], higher_is_better=True)
        else:
            df["norm_opp"] = 0.5

        if "tournament_history" in df.columns:
            df["norm_tournament"] = self._normalize(df["tournament_history"], higher_is_better=True)
        else:
            df["norm_tournament"] = 0.5

        df["igf_score_raw"] = (
            self.config.elo_weight * df["norm_elo"]
            + self.config.recent_form_weight * df["norm_form"]
            + self.config.xg_weight * df["norm_xg"]
            + self.config.xga_weight * df["norm_xga"]
            + self.config.opponent_strength_weight * df["norm_opp"]
            + self.config.world_cup_experience_weight * df["norm_wc_exp"]
            + self.config.squad_quality_weight * df["norm_squad"]
            + self.config.tournament_history_weight * df["norm_tournament"]
        )

        # Scale to 0-100
        min_raw = df["igf_score_raw"].min()
        max_raw = df["igf_score_raw"].max()
        if max_raw > min_raw:
            df["igf_score"] = ((df["igf_score_raw"] - min_raw) / (max_raw - min_raw)) * 100
        else:
            df["igf_score"] = 50.0

        df = df.sort_values("igf_score", ascending=False)
        df["igf_rank"] = range(1, len(df) + 1)

        return df

    def compute_team_scores(self, data: pd.DataFrame) -> dict[str, dict]:
        """Returns per-team component breakdown with 0-100 scale."""
        df = self.compute(data)
        result = {}
        for _, row in df.iterrows():
            result[row.get("team_name", str(row.name))] = {
                "igf_score": round(row["igf_score"], 2),
                "igf_rank": int(row["igf_rank"]),
                "components": {
                    "elo": round(row.get("norm_elo", 0) * 100, 2),
                    "form": round(row.get("norm_form", 0) * 100, 2),
                    "xg": round(row.get("norm_xg", 0) * 100, 2),
                    "xga": round(row.get("norm_xga", 0) * 100, 2),
                    "opponent_strength": round(row.get("norm_opp", 0) * 100, 2),
                    "wc_experience": round(row.get("norm_wc_exp", 0) * 100, 2),
                    "squad_quality": round(row.get("norm_squad", 0) * 100, 2),
                    "tournament_history": round(row.get("norm_tournament", 0) * 100, 2),
                },
            }
        return result

    @staticmethod
    def _normalize(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
        min_v, max_v = series.min(), series.max()
        if max_v == min_v:
            return pd.Series(0.5, index=series.index)
        if higher_is_better:
            return (series - min_v) / (max_v - min_v)
        return (max_v - series) / (max_v - min_v)
