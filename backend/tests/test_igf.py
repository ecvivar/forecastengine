import pandas as pd

from app.engine.igf import IGFEngine, IGFConfig


class TestIGFEngine:
    def setup_method(self):
        self.engine = IGFEngine(IGFConfig())

    def test_compute_with_minimal_data(self):
        data = pd.DataFrame({
            "team_name": ["Team A", "Team B", "Team C"],
            "elo_score": [1500, 1600, 1700],
            "fifa_rank": [3, 2, 1],
            "xg_for": [1.5, 2.0, 2.5],
            "xg_against": [1.2, 1.0, 0.8],
        })
        result = self.engine.compute(data)
        assert "igf_score" in result.columns
        assert "igf_rank" in result.columns
        assert len(result) == 3
        assert result.iloc[0]["igf_rank"] == 1

    def test_normalize_higher_better(self):
        s = pd.Series([1, 2, 3, 4, 5])
        normalized = IGFEngine._normalize(s, higher_is_better=True)
        assert normalized.iloc[0] == 0.0
        assert normalized.iloc[-1] == 1.0

    def test_normalize_lower_better(self):
        s = pd.Series([1, 2, 3, 4, 5])
        normalized = IGFEngine._normalize(s, higher_is_better=False)
        assert normalized.iloc[0] == 1.0
        assert normalized.iloc[-1] == 0.0

    def test_compute_team_scores(self):
        data = pd.DataFrame({
            "team_name": ["Team X"],
            "elo_score": [1600],
            "fifa_rank": [5],
            "xg_for": [2.0],
            "xg_against": [1.0],
        })
        scores = self.engine.compute_team_scores(data)
        assert "Team X" in scores
        assert "igf_score" in scores["Team X"]
        assert "components" in scores["Team X"]
