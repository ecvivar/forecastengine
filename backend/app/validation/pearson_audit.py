"""
Phase 6 — Pearson Correlation Audit.
Decomposes correlation by tournament stage to determine if decline is real or methodological.
"""
import numpy as np
from scipy.stats import pearsonr, spearmanr, kendalltau
from app.domain.entities import PredictionConfig
from app.engine.match_prediction import MatchPredictionEngine
from app.engine.monte_carlo import run_single_tournament_py
from app.data.historical_matches import ALL_HISTORICAL_MATCHES


class PearsonAudit:
    """Audit Pearson correlation decay by stage and sim count."""

    def __init__(self, config: PredictionConfig | None = None):
        self.config = config or PredictionConfig()
        self.engine = MatchPredictionEngine(config=self.config)

    def compute_strengths(self, teams: list, group_mapping: dict) -> tuple:
        strengths = np.array([
            self.engine.compute_team_strength(t).overall_strength
            for t in teams
        ], dtype=np.float64)
        str_list = [float(s) for s in strengths]
        group_names = [group_mapping.get(t.id, "?") for t in teams]
        unique = sorted(set(group_names))
        g2i = {g: i for i, g in enumerate(unique)}
        assignments = np.array([g2i[g] for g in group_names], dtype=np.int64)
        return strengths, str_list, assignments

    def simulate_tournament(self, strengths: np.ndarray, assignments: np.ndarray,
                            num_teams: int, n_sims: int = 10000) -> np.ndarray:
        won = np.zeros(num_teams, dtype=np.int32)
        r16 = np.zeros(num_teams, dtype=np.int32)
        qf = np.zeros(num_teams, dtype=np.int32)
        sf = np.zeros(num_teams, dtype=np.int32)
        final = np.zeros(num_teams, dtype=np.int32)
        for _ in range(n_sims):
            sr = run_single_tournament_py(strengths, assignments, num_teams)
            for t in range(num_teams):
                stage = sr[t, 0]
                if stage >= 6: won[t] += 1
                if stage >= 5: final[t] += 1
                if stage >= 4: sf[t] += 1
                if stage >= 3: qf[t] += 1
                if stage >= 2: r16[t] += 1
        return {
            "champion": won.astype(float) / n_sims,
            "final": final.astype(float) / n_sims,
            "semi": sf.astype(float) / n_sims,
            "quarter": qf.astype(float) / n_sims,
            "r16": r16.astype(float) / n_sims,
        }

    def correlate(self, strengths: list, probs: np.ndarray,
                  name: str) -> dict:
        p, _ = pearsonr(strengths, probs)
        s, _ = spearmanr(strengths, probs)
        k, _ = kendalltau(strengths, probs)
        return {
            "stage": name,
            "pearson": round(float(p), 4),
            "spearman": round(float(s), 4),
            "kendall": round(float(k), 4),
        }

    def audit(self, teams: list, group_mapping: dict,
              n_sims: int = 5000) -> dict:
        strengths, str_list, assignments = self.compute_strengths(teams, group_mapping)
        num_teams = len(teams)
        probs = self.simulate_tournament(strengths, assignments, num_teams, n_sims)
        results = []
        for stage in ["champion", "final", "semi", "quarter", "r16"]:
            r = self.correlate(str_list, probs[stage], stage)
            results.append(r)
        return {
            "n_sims": n_sims,
            "n_teams": num_teams,
            "correlations": results,
            "mean_pearson": round(float(np.mean([r["pearson"] for r in results])), 4),
        }

    def sim_count_sweep(self, teams: list, group_mapping: dict,
                        sim_counts: list[int] | None = None) -> list[dict]:
        if sim_counts is None:
            sim_counts = [1000, 2000, 5000, 10000, 25000]
        sweeps = []
        for n in sim_counts:
            r = self.audit(teams, group_mapping, n)
            sweeps.append({"n_sims": n, "correlations": r["correlations"],
                           "mean_pearson": r["mean_pearson"]})
        return sweeps

    @staticmethod
    def summary_table(audit_result: dict) -> str:
        lines = ["# Pearson Correlation Audit\n",
                 f"**N Sims:** {audit_result['n_sims']:,}  |  **N Teams:** {audit_result['n_teams']}\n",
                 "| Stage | Pearson | Spearman | Kendall |",
                 "|-------|---------|----------|---------|"]
        for r in audit_result["correlations"]:
            lines.append(f"| {r['stage']} | {r['pearson']:.4f} | {r['spearman']:.4f} | {r['kendall']:.4f} |")
        lines.append(f"\n**Mean Pearson:** {audit_result['mean_pearson']:.4f}")
        return "\n".join(lines)

    @staticmethod
    def sweep_table(sweep_results: list[dict]) -> str:
        lines = ["# Monte Carlo Noise — Sim Count vs Correlation\n",
                 "| N Sims | Champion | Final | Semi | Quarter | R16 | Mean Pearson |",
                 "|--------|----------|-------|------|---------|-----|--------------|"]
        for sw in sweep_results:
            corr = {r["stage"]: r["pearson"] for r in sw["correlations"]}
            lines.append(f"| {sw['n_sims']:>6,} | {corr.get('champion', 0):.4f} | {corr.get('final', 0):.4f} | "
                         f"{corr.get('semi', 0):.4f} | {corr.get('quarter', 0):.4f} | "
                         f"{corr.get('r16', 0):.4f} | {sw['mean_pearson']:.4f} |")
        return "\n".join(lines)
