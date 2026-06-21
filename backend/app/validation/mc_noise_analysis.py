"""
Phase 7 — Monte Carlo Noise Analysis.
Evaluates convergence of Pearson, champion variance, and CI width as sim count increases.
"""
import numpy as np
from app.domain.entities import PredictionConfig
from app.engine.match_prediction import MatchPredictionEngine
from app.engine.monte_carlo import run_single_tournament_py


class MCNoiseAnalysis:
    """Analyze Monte Carlo noise vs simulation count."""

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MatchPredictionEngine(config=self.config)

    def run_sweep(self, teams: list, group_mapping: dict,
                  sim_counts: list[int] | None = None,
                  n_replicates: int = 3) -> list[dict]:
        if sim_counts is None:
            sim_counts = [1000, 2000, 5000, 10000, 25000, 50000]
        strengths = np.array([
            self.engine.compute_team_strength(t).overall_strength
            for t in teams
        ], dtype=np.float64)
        group_names = [group_mapping.get(t.id, "?") for t in teams]
        unique = sorted(set(group_names))
        g2i = {g: i for i, g in enumerate(unique)}
        assignments = np.array([g2i[g] for g in group_names], dtype=np.int64)
        num_teams = len(teams)

        results = []
        for n_sims in sim_counts:
            champ_probs_list = []
            pearson_list = []
            str_list = [float(s) for s in strengths]
            for _ in range(n_replicates):
                won = np.zeros(num_teams, dtype=np.int32)
                for _ in range(n_sims):
                    sr = run_single_tournament_py(strengths, assignments, num_teams)
                    for t in range(num_teams):
                        if sr[t, 0] >= 6: won[t] += 1
                champ_probs = won.astype(float) / n_sims
                champ_probs_list.append(champ_probs)
                corr = float(np.corrcoef(str_list, champ_probs)[0, 1])
                pearson_list.append(corr)

            all_champ = np.array(champ_probs_list)
            mean_probs = np.mean(all_champ, axis=0)
            champ_var = float(np.var(mean_probs))
            pearson_std = float(np.std(pearson_list))
            mean_pearson = float(np.mean(pearson_list))
            top_team_var = float(np.var([p[np.argmax(mean_probs)] for p in champ_probs_list]))

            results.append({
                "n_sims": n_sims,
                "mean_pearson": round(mean_pearson, 4),
                "pearson_std": round(pearson_std, 4),
                "champion_variance": round(champ_var, 6),
                "top_team_variance": round(top_team_var, 6),
            })
        return results

    @staticmethod
    def summary_table(sweep: list[dict]) -> str:
        lines = ["# Monte Carlo Noise Analysis\n",
                 "| N Sims | Mean Pearson | Pearson Std | Champion Var | Top Team Var |",
                 "|--------|--------------|-------------|--------------|--------------|"]
        for r in sweep:
            lines.append(f"| {r['n_sims']:>6,} | {r['mean_pearson']:.4f} | {r['pearson_std']:.4f} | "
                         f"{r['champion_variance']:.6f} | {r['top_team_variance']:.6f} |")
        lines.append("\n**Stability Criterion:** Pearson Std < 0.01 indicates convergence.")
        return "\n".join(lines)

    @staticmethod
    def find_convergence_point(sweep: list[dict], threshold: float = 0.01) -> dict:
        for r in sweep:
            if r["pearson_std"] < threshold:
                return {"converged_at": r["n_sims"], "pearson_std": r["pearson_std"],
                        "mean_pearson": r["mean_pearson"], "threshold": threshold}
        return {"converged_at": None, "pearson_std": sweep[-1]["pearson_std"],
                "mean_pearson": sweep[-1]["mean_pearson"], "threshold": threshold}
