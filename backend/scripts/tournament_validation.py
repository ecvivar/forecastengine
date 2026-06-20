"""
Sprint 7.5 — Full Tournament Validation.
Compares elo=0.40 vs elo=0.32 on 48-team Monte Carlo pipeline.

Metrics:
  - Stress Std (perturb 48 teams × N scenarios, re-run 10k sims each)
  - ECE (match-level predictions vs historical outcomes)
  - CI Coverage (bootstrap percentile intervals)
  - Pearson (overall_strength vs champion_prob)
  - Sharpness (avg entropy of match predictions)
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

# ── Helper: run N tournament sims ──────────────────────────────────────────
def run_tournament_batch(teams, group_mapping, config, n_sims, start_seed=42):
    mpe = MatchPredictionEngine(config=config)
    strengths = np.array(
        [mpe.compute_team_strength(t).overall_strength for t in teams],
        dtype=np.float64,
    )
    group_names = [group_mapping.get(t.id, "?") for t in teams]
    unique = sorted(set(group_names))
    g2i = {g: i for i, g in enumerate(unique)}
    assignments = np.array([g2i[g] for g in group_names], dtype=np.int64)
    num_teams = len(teams)
    counts = np.zeros((num_teams, 6), dtype=np.int32)  # R32,R16,QF,SF,Final,Won

    for sim in range(n_sims):
        sr = run_single_tournament_py(strengths, assignments, num_teams,
                                       seed=(start_seed + sim if start_seed else None))
        for t in range(num_teams):
            st = sr[t, 0]
            if st >= 1: counts[t, 0] += 1
            if st >= 2: counts[t, 1] += 1
            if st >= 3: counts[t, 2] += 1
            if st >= 4: counts[t, 3] += 1
            if st >= 5: counts[t, 4] += 1
            if st >= 6: counts[t, 5] += 1
        if (sim + 1) % 2000 == 0:
            logger.info(f"    {sim+1}/{n_sims} sims")

    champ_probs = {}
    for i, t in enumerate(teams):
        champ_probs[t.name] = float(counts[i, 5]) / n_sims
    return champ_probs, strengths, assignments

# ── Match-level predictions from historical data ───────────────────────────
def build_historical_team_entities():
    team_data = {}
    for m in ALL_HISTORICAL_MATCHES:
        for side in ("home", "away"):
            name = getattr(m, f"{side}_team")
            elo = getattr(m, f"{side}_elo")
            gf = m.home_goals if side == "home" else m.away_goals
            ga = m.away_goals if side == "home" else m.home_goals
            if name not in team_data:
                team_data[name] = {"elo": elo, "gf": [], "ga": []}
            team_data[name]["gf"].append(gf)
            team_data[name]["ga"].append(ga)

    entities = {}
    for name, d in team_data.items():
        avg_gf = float(np.mean(d["gf"])) if d["gf"] else 1.0
        avg_ga = float(np.mean(d["ga"])) if d["ga"] else 1.5
        est_rank = max(1, min(100, int(100 * (1 - (d["elo"] - 1300) / 800))))
        entities[name] = TeamEntity(
            id=uuid.uuid4(), name=name, elo_score=d["elo"],
            fifa_rank=est_rank, xg_for=round(avg_gf, 4),
            xg_against=round(avg_ga, 4),
        )
    return entities

def match_predictions(config):
    hist_entities = build_historical_team_entities()
    mpe = MatchPredictionEngine(config=config)
    probs, outcomes = [], []
    for m in ALL_HISTORICAL_MATCHES:
        home = hist_entities.get(m.home_team)
        away = hist_entities.get(m.away_team)
        if not home or not away:
            continue
        r = mpe.predict_full(home, away)
        probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
        if m.home_goals > m.away_goals:
            outcomes.append([1, 0, 0])
        elif m.home_goals == m.away_goals:
            outcomes.append([0, 1, 0])
        else:
            outcomes.append([0, 0, 1])
    return np.array(probs), np.array(outcomes)

# ── CI Coverage via bootstrap ──────────────────────────────────────────────
def bootstrap_ci_coverage(config, n_matches=100, n_resamples=200):
    hist_entities = build_historical_team_entities()
    mpe = MatchPredictionEngine(config=config)
    np.random.seed(42)
    covered, total = 0, 0

    match_list = [(m.home_team, m.away_team, m.home_goals, m.away_goals)
                  for m in ALL_HISTORICAL_MATCHES
                  if m.home_team in hist_entities and m.away_team in hist_entities]
    np.random.shuffle(match_list)
    match_list = match_list[:n_matches]

    for home_name, away_name, hg, ag in match_list:
        home, away = hist_entities[home_name], hist_entities[away_name]
        point = mpe.predict_full(home, away)

        # Bootstrap resamples
        samp_hw, samp_d, samp_aw = [], [], []
        for _ in range(n_resamples):
            h, a = deepcopy(home), deepcopy(away)
            h.elo_score = int(h.elo_score * np.random.uniform(0.85, 1.15))
            a.elo_score = int(a.elo_score * np.random.uniform(0.85, 1.15))
            if h.xg_for: h.xg_for *= np.random.uniform(0.80, 1.20)
            if a.xg_for: a.xg_for *= np.random.uniform(0.80, 1.20)
            if h.xg_against: h.xg_against *= np.random.uniform(0.80, 1.20)
            if a.xg_against: a.xg_against *= np.random.uniform(0.80, 1.20)
            h.fifa_rank = max(1, int((h.fifa_rank or 50) * np.random.uniform(0.8, 1.2)))
            a.fifa_rank = max(1, int((a.fifa_rank or 50) * np.random.uniform(0.8, 1.2)))

            r = mpe.predict_full(h, a)
            samp_hw.append(r.home_win_prob)
            samp_d.append(r.draw_prob)
            samp_aw.append(r.away_win_prob)

        for probs_list, actual in [
            (samp_hw, 1.0 if hg > ag else 0.0),
            (samp_d, 1.0 if hg == ag else 0.0),
            (samp_aw, 1.0 if hg < ag else 0.0),
        ]:
            lo = float(np.percentile(probs_list, 5))
            hi = float(np.percentile(probs_list, 95))
            total += 1
            if lo <= actual <= hi:
                covered += 1

    return covered / max(total, 1)

# ── Tournament Stress Test ─────────────────────────────────────────────────
def tournament_stress_test(teams, group_mapping, config, n_stress=100, n_sims_per=2000, start_seed=42):
    mpe = MatchPredictionEngine(config=config)
    np.random.seed(start_seed)

    # Baseline strengths
    base_strengths = np.array(
        [mpe.compute_team_strength(t).overall_strength for t in teams], dtype=np.float64,
    )
    group_names = [group_mapping.get(t.id, "?") for t in teams]
    unique = sorted(set(group_names))
    g2i = {g: i for i, g in enumerate(unique)}
    assignments = np.array([g2i[g] for g in group_names], dtype=np.int64)
    num_teams = len(teams)

    # Baseline champion probabilities
    base_counts = np.zeros(num_teams, dtype=np.int32)
    seed = start_seed
    for sim in range(n_sims_per):
        sr = run_single_tournament_py(base_strengths, assignments, num_teams, seed=seed)
        for t in range(num_teams):
            if sr[t, 0] >= 6: base_counts[t] += 1
        seed += 1
    base_champ = {teams[i].name: float(base_counts[i]) / n_sims_per for i in range(num_teams)}

    # Stress scenarios
    stress_champ = {t.name: [] for t in teams}
    for sc in range(n_stress):
        # Perturb team entities
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
        sc_counts = np.zeros(num_teams, dtype=np.int32)
        for sim in range(n_sims_per):
            sr = run_single_tournament_py(stress_str, assignments, num_teams, seed=seed)
            for t in range(num_teams):
                if sr[t, 0] >= 6: sc_counts[t] += 1
            seed += 1
        for i, t in enumerate(teams):
            stress_champ[t.name].append(float(sc_counts[i]) / n_sims_per)

        if (sc + 1) % 10 == 0:
            logger.info(f"    Stress scenario {sc+1}/{n_stress}")

    stress_std = {name: float(np.std(probs)) for name, probs in stress_champ.items()}
    return base_champ, stress_std

# ── Compare two configs ────────────────────────────────────────────────────
def evaluate_config(label, config, teams, group_mapping):
    print(f"\n{'='*60}")
    print(f"  CONFIG: {label} (elo={config.elo_weight})")
    print(f"{'='*60}")

    # A - Match-level predictions (ECE + Sharpness)
    logger.info("Step A — Match-level predictions (ECE, Sharpness)")
    t0 = time.time()
    pa, oa = match_predictions(config)
    ece_val, _ = metrics.expected_calibration_error(pa, oa)
    sharpness_val = sharp.average_entropy(pa)
    brier_val = metrics.brier_score(pa, oa)
    logloss_val = metrics.log_loss(pa, oa)
    rps_val = metrics.ranked_probability_score(pa, oa)
    acc_val = float(np.mean(np.argmax(pa, axis=1) == np.argmax(oa, axis=1)))
    print(f"    Matches: {len(pa)}")
    print(f"    Accuracy: {acc_val*100:.2f}%")
    print(f"    Brier: {brier_val:.4f}")
    print(f"    LogLoss: {logloss_val:.4f}")
    print(f"    RPS: {rps_val:.4f}")
    print(f"    ECE: {ece_val:.4f}")
    print(f"    Sharpness: {sharpness_val:.4f}")
    match_time = time.time() - t0
    print(f"    Time: {match_time:.1f}s")

    # B - Baseline tournament
    logger.info("Step B — Baseline tournament (10k sims)")
    t0 = time.time()
    champ_probs, strengths, _ = run_tournament_batch(teams, group_mapping, config, 10_000)
    tourn_time = time.time() - t0
    print(f"    Time: {tourn_time:.1f}s")

    top5 = sorted(champ_probs.items(), key=lambda x: -x[1])[:5]
    print(f"    Top 5 champions:")
    for name, prob in top5:
        print(f"      {name}: {prob*100:.2f}%")
    champ_sum = sum(champ_probs.values())
    print(f"    Sum of champion probs: {champ_sum:.2f}%")
    assert abs(champ_sum - 1.0) < 0.01, f"Sum={champ_sum} != 1.0"

    # C - Pearson: strength vs champion prob
    strength_list = [strengths[i] for i in range(len(teams))]
    champ_list = [champ_probs[t.name] for t in teams]
    pearson_r = float(np.corrcoef(strength_list, champ_list)[0, 1])
    print(f"    Pearson (strength vs champion): {pearson_r:.4f}")

    # D - CI Coverage
    logger.info("Step D — CI Coverage (bootstrap, 100 matches)")
    t0 = time.time()
    coverage = bootstrap_ci_coverage(config, n_matches=100, n_resamples=200)
    ci_time = time.time() - t0
    print(f"    CI Coverage (90% nominal): {coverage*100:.1f}%")
    print(f"    Time: {ci_time:.1f}s")

    # E - Tournament Stress Test
    logger.info(f"Step E — Tournament Stress Test (50 scenarios x 2k sims)")
    t0 = time.time()
    base_champ, stress_std = tournament_stress_test(
        teams, group_mapping, config, n_stress=50, n_sims_per=2000,
    )
    stress_time = time.time() - t0
    avg_stress = float(np.mean(list(stress_std.values())))
    max_stress = float(np.max(list(stress_std.values())))
    print(f"    Stress Std (avg across 48 teams): {avg_stress:.4f}")
    print(f"    Stress Std (max across 48 teams): {max_stress:.4f}")
    print(f"    Time: {stress_time:.1f}s")

    return {
        "label": label,
        "elo_weight": config.elo_weight,
        "accuracy": round(acc_val, 4),
        "brier": round(brier_val, 4),
        "logloss": round(logloss_val, 4),
        "rps": round(rps_val, 4),
        "ece": round(ece_val, 4),
        "sharpness": round(sharpness_val, 4),
        "pearson": round(pearson_r, 4),
        "ci_coverage": round(coverage, 4),
        "stress_std_avg": round(avg_stress, 4),
        "stress_std_max": round(max_stress, 4),
        "top5_champions": [(n, round(p*100, 2)) for n, p in top5],
        "timing": {
            "match_predictions": round(match_time, 1),
            "tournament_baseline": round(tourn_time, 1),
            "ci_coverage": round(ci_time, 1),
            "stress_test": round(stress_time, 1),
        },
    }

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  SPRINT 7.5 — FULL TOURNAMENT VALIDATION")
    print("  48 teams, 10k sims, 50 stress scenarios")
    print("=" * 60)

    teams, group_mapping = build_teams()
    print(f"\nTeams: {len(teams)}, Groups: {len(set(group_mapping.values()))}")
    for g in "ABCDEFGHIJKL":
        gteams = [t.name for t in teams if group_mapping.get(t.id) == g]
        print(f"  Group {g}: {', '.join(gteams)}")

    cfg_040 = PredictionConfig(
        elo_weight=0.40, xg_attack_weight=0.30,
        xg_defense_weight=0.20, fifa_weight=0.10,
    )
    cfg_032 = PredictionConfig(
        elo_weight=0.32, xg_attack_weight=0.35,
        xg_defense_weight=0.23, fifa_weight=0.10,
    )

    results = {}
    for label, cfg in [("Sprint 7 (elo=0.40)", cfg_040),
                        ("Sprint 7.5 (elo=0.32)", cfg_032)]:
        results[label] = evaluate_config(label, cfg, teams, group_mapping)

    # Comparison table
    print(f"\n{'='*60}")
    print(f"  COMPARISON: elo=0.40 vs elo=0.32")
    print(f"{'='*60}")
    metrics_list = ["accuracy", "brier", "logloss", "rps", "ece", "sharpness",
                     "pearson", "ci_coverage", "stress_std_avg", "stress_std_max"]
    print(f"  {'Metric':25s} {'elo=0.40':>12s} {'elo=0.32':>12s} {'Delta':>12s}")
    print(f"  {'-'*61}")
    for m in metrics_list:
        v40 = results["Sprint 7 (elo=0.40)"][m]
        v32 = results["Sprint 7.5 (elo=0.32)"][m]
        if isinstance(v40, float) and isinstance(v32, float):
            delta = v32 - v40
        else:
            delta = 0
        unit = "%" if m in ("accuracy", "ci_coverage") else ""
        print(f"  {m:25s} {v40:11.4f}{unit} {v32:11.4f}{unit} {delta:+11.4f}{unit}")

    # Save
    out = DOCS / "tournament_validation_comparison.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {out}")

    print(f"\nDone.")

if __name__ == "__main__":
    main()
