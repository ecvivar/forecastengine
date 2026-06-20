"""
Sprint 7.5 — Full Tournament Validation (v2).
Compares elo=0.40 vs elo=0.32 on 48-team Monte Carlo pipeline.

Metrics:
  - Stress Std: std of champion prob across perturbed scenarios
  - ECE: match-level expected calibration error
  - CI Coverage: % of teams where 10k-sim champ prob falls in stress bootstrap 90% CI
  - Pearson: overall_strength vs champion_prob correlation
  - Sharpness: avg entropy of match predictions
"""
import json, logging, os, sys, time, uuid
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

import numpy as np

from app.engine.match_prediction import MatchPredictionEngine
from app.engine.monte_carlo import run_single_tournament_py
from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig, TeamEntity
from app.validation.calibration_metrics import CalibrationMetrics
from app.engine.sprint5_modules import SharpnessMetrics

DOCS = Path(__file__).resolve().parent.parent / "docs"
DOCS.mkdir(exist_ok=True)
metrics = CalibrationMetrics()
sharp = SharpnessMetrics()

# ── 48 realistic teams ──────────────────────────────────────────────────────
TEAMS_DATA = [
    ("Brazil", 1942, 1, 2.30, 0.85),    ("Argentina", 1915, 2, 2.10, 0.90),
    ("France", 1900, 3, 2.20, 0.80),     ("England", 1885, 4, 2.00, 0.95),
    ("Spain", 1870, 5, 2.05, 0.88),      ("Germany", 1860, 6, 1.95, 0.92),
    ("Netherlands", 1850, 7, 1.90, 0.90),("Portugal", 1840, 8, 1.85, 0.95),
    ("Italy", 1830, 9, 1.80, 1.00),      ("Belgium", 1820, 10, 1.85, 1.05),
    ("Croatia", 1810, 11, 1.70, 1.00),   ("Uruguay", 1800, 12, 1.65, 1.05),
    ("Colombia", 1780, 13, 1.60, 1.10),  ("Denmark", 1770, 14, 1.55, 1.05),
    ("Switzerland", 1760, 15, 1.50, 1.10),("Mexico", 1750, 16, 1.55, 1.15),
    ("Japan", 1740, 17, 1.45, 1.10),     ("Morocco", 1730, 18, 1.40, 1.15),
    ("Senegal", 1720, 19, 1.45, 1.20),   ("USA", 1710, 20, 1.50, 1.25),
    ("Serbia", 1700, 21, 1.40, 1.20),    ("Poland", 1690, 22, 1.45, 1.25),
    ("South Korea", 1680, 23, 1.35, 1.20),("Nigeria", 1670, 24, 1.40, 1.25),
    ("Ecuador", 1660, 25, 1.35, 1.25),   ("Iran", 1650, 26, 1.20, 1.15),
    ("Australia", 1640, 27, 1.25, 1.30), ("Canada", 1630, 28, 1.30, 1.30),
    ("Costa Rica", 1620, 29, 1.15, 1.25),("Cameroon", 1610, 30, 1.25, 1.35),
    ("Ghana", 1600, 31, 1.30, 1.35),     ("Saudi Arabia", 1580, 32, 1.10, 1.30),
    ("Tunisia", 1570, 33, 1.15, 1.35),   ("Algeria", 1560, 34, 1.20, 1.40),
    ("Egypt", 1550, 35, 1.15, 1.40),     ("Paraguay", 1540, 36, 1.10, 1.35),
    ("Panama", 1530, 37, 1.05, 1.40),    ("Slovakia", 1520, 38, 1.10, 1.45),
    ("Hungary", 1510, 39, 1.15, 1.45),   ("Greece", 1500, 40, 1.10, 1.40),
    ("Norway", 1490, 41, 1.20, 1.50),    ("Scotland", 1480, 42, 1.05, 1.45),
    ("Venezuela", 1470, 43, 1.00, 1.50), ("China", 1460, 44, 0.95, 1.50),
    ("Iraq", 1450, 45, 0.90, 1.55),      ("New Zealand", 1440, 46, 0.85, 1.50),
    ("Indonesia", 1430, 47, 0.80, 1.60), ("Kuwait", 1420, 48, 0.75, 1.65),
]

def build_teams():
    teams = []
    for name, elo, rank, xgf, xga in TEAMS_DATA:
        teams.append(TeamEntity(
            id=uuid.uuid4(), name=name, fifa_code=name[:3].upper(),
            elo_score=elo, fifa_rank=rank, xg_for=xgf, xg_against=xga,
        ))
    groups = "ABCDEFGHIJKL"
    group_mapping = {t.id: groups[i % 12] for i, t in enumerate(teams)}
    return teams, group_mapping

# ── Historical team entities for match-level metrics ───────────────────────
def build_historical_entities():
    td = {}
    for m in ALL_HISTORICAL_MATCHES:
        for side in ("home", "away"):
            name = getattr(m, f"{side}_team")
            elo = getattr(m, f"{side}_elo")
            gf = m.home_goals if side == "home" else m.away_goals
            ga = m.away_goals if side == "home" else m.home_goals
            if name not in td:
                td[name] = {"elo": elo, "gf": [], "ga": []}
            td[name]["gf"].append(gf); td[name]["ga"].append(ga)
    entities = {}
    for name, d in td.items():
        avg_gf = float(np.mean(d["gf"])) if d["gf"] else 1.0
        avg_ga = float(np.mean(d["ga"])) if d["ga"] else 1.5
        est_rank = max(1, min(100, int(100 * (1 - (d["elo"] - 1300) / 800))))
        entities[name] = TeamEntity(
            id=uuid.uuid4(), name=name, elo_score=d["elo"],
            fifa_rank=est_rank, xg_for=round(avg_gf, 4),
            xg_against=round(avg_ga, 4),
        )
    return entities

# ── Phase 1: Match-level ECE + Sharpness ───────────────────────────────────
def phase_match_level(config):
    hist = build_historical_entities()
    mpe = MatchPredictionEngine(config=config)
    probs, outcomes = [], []
    for m in ALL_HISTORICAL_MATCHES:
        home = hist.get(m.home_team)
        away = hist.get(m.away_team)
        if not home or not away: continue
        r = mpe.predict_full(home, away)
        probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
        if m.home_goals > m.away_goals:
            outcomes.append([1, 0, 0])
        elif m.home_goals == m.away_goals:
            outcomes.append([0, 1, 0])
        else:
            outcomes.append([0, 0, 1])
    pa = np.array(probs); oa = np.array(outcomes)
    return {
        "n_matches": len(pa),
        "accuracy": float(np.mean(np.argmax(pa, axis=1) == np.argmax(oa, axis=1))),
        "brier": metrics.brier_score(pa, oa),
        "logloss": metrics.log_loss(pa, oa),
        "rps": metrics.ranked_probability_score(pa, oa),
        "ece": metrics.expected_calibration_error(pa, oa)[0],
        "sharpness": sharp.average_entropy(pa),
    }

# ── Phase 2: Baseline tournament (10k sims) ────────────────────────────────
def phase_baseline_tournament(teams, group_mapping, config, n_sims=10_000):
    """Run baseline tournament. Returns champ probs + per-chunk counts for CI validation."""
    mpe = MatchPredictionEngine(config=config)
    strengths = np.array(
        [mpe.compute_team_strength(t).overall_strength for t in teams], dtype=np.float64,
    )
    group_names = [group_mapping.get(t.id, "?") for t in teams]
    unique_groups = sorted(set(group_names))
    g2i = {g: i for i, g in enumerate(unique_groups)}
    assignments = np.array([g2i[g] for g in group_names], dtype=np.int64)
    num_teams = len(teams)

    # Track per-chunk counts for CI validation (100 chunks of n_sims//100 each)
    n_chunks = 100
    chunk_size = n_sims // n_chunks
    chunk_won = np.zeros((n_chunks, num_teams), dtype=np.int32)
    won = np.zeros(num_teams, dtype=np.int32)

    for sim in range(n_sims):
        sr = run_single_tournament_py(strengths, assignments, num_teams)
        chunk_idx = min(sim // chunk_size, n_chunks - 1)
        for t in range(num_teams):
            if sr[t, 0] >= 6:
                won[t] += 1
                chunk_won[chunk_idx, t] += 1

    champ = {teams[i].name: float(won[i]) / n_sims for i in range(num_teams)}

    # CI coverage from chunk bootstrap
    ci_covered = 0
    for t in range(num_teams):
        chunk_probs = chunk_won[:, t].astype(float) / chunk_size
        lo = float(np.percentile(chunk_probs, 5))
        hi = float(np.percentile(chunk_probs, 95))
        true_val = float(won[t]) / n_sims
        if lo <= true_val <= hi:
            ci_covered += 1

    return champ, strengths, assignments, ci_covered / num_teams

# ── Phase 3: Tournament Stress Test + CI Coverage ──────────────────────────
def phase_stress_test(teams, group_mapping, config, n_stress=100, n_sims_per=5_000):
    mpe = MatchPredictionEngine(config=config)
    np.random.seed(42)

    # Build baseline strengths / assignments
    strengths = np.array(
        [mpe.compute_team_strength(t).overall_strength for t in teams], dtype=np.float64,
    )
    group_names = [group_mapping.get(t.id, "?") for t in teams]
    unique = sorted(set(group_names))
    g2i = {g: i for i, g in enumerate(unique)}
    assignments = np.array([g2i[g] for g in group_names], dtype=np.int64)
    num_teams = len(teams)

    # Baseline champion probs (high precision)
    base_won = np.zeros(num_teams, dtype=np.int32)
    for sim in range(10_000):
        sr = run_single_tournament_py(strengths, assignments, num_teams)
        for t in range(num_teams):
            if sr[t, 0] >= 6: base_won[t] += 1
    baseline = {teams[i].name: float(base_won[i]) / 10_000 for i in range(num_teams)}

    # Stress scenarios
    stress_counts = {t.name: [] for t in teams}
    for sc in range(n_stress):
        perturbed = []
        for t in teams:
            pt = deepcopy(t)
            pt.elo_score = int(t.elo_score * np.random.uniform(0.85, 1.15))
            if pt.xg_for: pt.xg_for *= np.random.uniform(0.80, 1.20)
            if pt.xg_against: pt.xg_against *= np.random.uniform(0.80, 1.20)
            pt.fifa_rank = max(1, int((t.fifa_rank or 50) * np.random.uniform(0.8, 1.2)))
            perturbed.append(pt)
        stress_str = np.array(
            [mpe.compute_team_strength(pt).overall_strength for pt in perturbed], dtype=np.float64,
        )
        sc_won = np.zeros(num_teams, dtype=np.int32)
        for sim in range(n_sims_per):
            sr = run_single_tournament_py(stress_str, assignments, num_teams)
            for t in range(num_teams):
                if sr[t, 0] >= 6: sc_won[t] += 1
        for i, t in enumerate(teams):
            stress_counts[t.name].append(float(sc_won[i]) / n_sims_per)
        if (sc + 1) % 20 == 0:
            logger.info(f"      Stress {sc+1}/{n_stress}")

    # Compute metrics from stress data
    stress_std = {}
    ci_covered = 0
    for t in teams:
        probs = np.array(stress_counts[t.name])
        stress_std[t.name] = float(np.std(probs))
        lo, hi = float(np.percentile(probs, 5)), float(np.percentile(probs, 95))
        if lo <= baseline[t.name] <= hi:
            ci_covered += 1

    return {
        "stress_std_avg": float(np.mean(list(stress_std.values()))),
        "stress_std_max": float(np.max(list(stress_std.values()))),
        "ci_coverage": ci_covered / len(teams),
        "baseline_champ": baseline,
        "stress_champ_samples": stress_counts,
    }

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 66)
    print("  SPRINT 7.5 — FULL TOURNAMENT VALIDATION (v2)")
    print("  48 teams | 10k base sims | 100 stress x 5k sims")
    print("=" * 66)

    teams, group_mapping = build_teams()
    print(f"\nTeams: {len(teams)}, Groups: {len(set(group_mapping.values()))}")

    cfgs = [
        ("Sprint 7  (elo=0.40)", PredictionConfig(elo_weight=0.40, xg_attack_weight=0.30, xg_defense_weight=0.20, fifa_weight=0.10)),
        ("Sprint 7.5 (elo=0.32)", PredictionConfig(elo_weight=0.32, xg_attack_weight=0.35, xg_defense_weight=0.23, fifa_weight=0.10)),
    ]

    all_results = {}
    for label, cfg in cfgs:
        print(f"\n{'='*66}")
        print(f"  {label}")
        print(f"{'='*66}")

        # Phase 1 — Match-level
        logger.info("Phase 1 — Match-level ECE + Sharpness")
        t0 = time.time()
        ml = phase_match_level(cfg)
        print(f"    Matches: {ml['n_matches']} | Acc: {ml['accuracy']*100:.2f}% | "
              f"Brier: {ml['brier']:.4f} | ECE: {ml['ece']:.4f} | Sharp: {ml['sharpness']:.4f}")
        t_match = time.time() - t0

        # Phase 2 — Baseline tournament
        logger.info("Phase 2 — Baseline tournament 10k sims")
        t0 = time.time()
        champ_base, strengths, _, ci_coverage = phase_baseline_tournament(
            teams, group_mapping, cfg, 10_000
        )
        top5 = sorted(champ_base.items(), key=lambda x: -x[1])[:5]
        print(f"    Top 5: {', '.join(f'{n} {p*100:.2f}%' for n,p in top5)}")
        print(f"    CI Coverage (chunk bootstrap 90%): {ci_coverage*100:.1f}%")
        assert abs(sum(champ_base.values()) - 1.0) < 0.01
        t_baseline = time.time() - t0

        # Pearson: strength vs champion prob
        str_list = [strengths[i] for i in range(len(teams))]
        champ_list = [champ_base[t.name] for t in teams]
        pearson_r = float(np.corrcoef(str_list, champ_list)[0, 1])
        print(f"    Pearson(strength, champion): {pearson_r:.4f}")

        # Phase 3 — Stress test + CI Coverage
        logger.info("Phase 3 — Stress test (100 scenarios x 5k sims)")
        t0 = time.time()
        stress = phase_stress_test(teams, group_mapping, cfg, n_stress=100, n_sims_per=5_000)
        t_stress = time.time() - t0
        print(f"    Stress Std (avg): {stress['stress_std_avg']:.6f}")
        print(f"    Stress Std (max): {stress['stress_std_max']:.6f}")
        print(f"    CI Coverage: {stress['ci_coverage']*100:.1f}%")

        all_results[label] = {
            "elo_weight": cfg.elo_weight,
            "accuracy": round(ml["accuracy"], 4),
            "brier": round(ml["brier"], 4),
            "ece": round(ml["ece"], 4),
            "sharpness": round(ml["sharpness"], 4),
            "pearson": round(pearson_r, 4),
            "stress_std_avg": round(stress["stress_std_avg"], 6),
            "stress_std_max": round(stress["stress_std_max"], 6),
            "ci_coverage_stress": round(stress["ci_coverage"], 4),
            "ci_coverage_chunk": round(ci_coverage, 4),
            "top5": [(n, round(p*100, 2)) for n, p in top5],
            "timing": {"match": round(t_match, 1), "baseline": round(t_baseline, 1), "stress": round(t_stress, 1)},
        }

    # Comparison
    print(f"\n{'='*66}")
    print(f"  COMPARISON")
    print(f"{'='*66}")
    keys = ["accuracy", "brier", "ece", "sharpness", "pearson",
            "stress_std_avg", "stress_std_max", "ci_coverage_chunk", "ci_coverage_stress"]
    print(f"  {'Metric':25s} {'elo=0.40':>14s} {'elo=0.32':>14s} {'Delta':>14s}")
    print(f"  {'-'*67}")
    for k in keys:
        v40 = all_results["Sprint 7  (elo=0.40)"][k]
        v32 = all_results["Sprint 7.5 (elo=0.32)"][k]
        delta = v32 - v40
        print(f"  {k:25s} {v40:14.6f} {v32:14.6f} {delta:+14.6f}")

    with open(DOCS / "tournament_validation_v2.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults: {DOCS / 'tournament_validation_v2.json'}")

    # Assessment — note: targets from Sprint 7.5 used different methodology
    r40 = all_results["Sprint 7  (elo=0.40)"]
    r32 = all_results["Sprint 7.5 (elo=0.32)"]
    print(f"\n{'='*66}")
    print(f"  ASSESSMENT vs PROFESSIONAL GRADE TARGETS")
    print(f"  (targets from match-level Sprint 7.5; here tournament-level)")
    print(f"{'='*66}")
    criteria = [
        ("Accuracy > 50%", 0.50, r32["accuracy"], False),
        ("ECE < 0.045", 0.045, r32["ece"], True),
        ("Tourn Stress Std < 0.07", 0.07, r32["stress_std_avg"], True),
        ("CI Coverage 85-95% (chunk)", (0.85, 0.95), r32["ci_coverage_chunk"], None),
        ("Pearson > 0.95", 0.95, r32["pearson"], False),
    ]
    passed = 0
    for entry in criteria:
        name, target, actual, cmp = entry
        if isinstance(target, tuple):
            ok = target[0] <= actual <= target[1]
        elif cmp is True:
            ok = actual < target
        elif cmp is False:
            ok = actual > target
        else:
            ok = False
        sym = "PASS" if ok else "FAIL"
        passed += ok
        print(f"  {name:30s} target={str(target):12s} actual={actual:.4f} [{sym}]")
    print(f"\n  Grade: {passed}/5 criteria met (note: methodology differs from Sprint 7.5)")

if __name__ == "__main__":
    main()
