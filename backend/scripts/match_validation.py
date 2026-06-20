"""
Sprint 3 — FASE 4: Match Prediction Validation.

Validates individual match predictions against all three World Cups.
Accumulates metrics: accuracy, Brier Score, Log Loss, ECE, calibration curve.

Output: docs/match_validation.md
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LOG_LEVEL"] = "WARNING"

import numpy as np

from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig
from app.engine.match_prediction import MatchPredictionEngine
from app.validation.backtesting import BacktestingEngine
from app.validation.calibration_metrics import CalibrationMetrics


def main():
    metrics = CalibrationMetrics()
    engine = MatchPredictionEngine()
    backtester = BacktestingEngine()

    all_probs = []
    all_outcomes = []
    match_details = []
    correct = 0
    total = 0

    for tournament in ("2014", "2018", "2022"):
        matches = [m for m in ALL_HISTORICAL_MATCHES if m.tournament == tournament]
        team_data = backtester._extract_team_data(matches)
        teams = {name: backtester._build_team_entity(name, d) for name, d in team_data.items()}

        for m in matches:
            home = teams.get(m.home_team)
            away = teams.get(m.away_team)
            if not home or not away:
                continue

            r = engine.predict_full(home, away, home_advantage=True)

            # Determine actual outcome
            if m.home_goals > m.away_goals:
                actual_label = "home"
                actual_vec = [1, 0, 0]
            elif m.home_goals == m.away_goals:
                actual_label = "draw"
                actual_vec = [0, 1, 0]
            else:
                actual_label = "away"
                actual_vec = [0, 0, 1]

            pred_label = "home" if r.home_win_prob >= r.draw_prob and r.home_win_prob >= r.away_win_prob else \
                         "draw" if r.draw_prob >= r.home_win_prob and r.draw_prob >= r.away_win_prob else \
                         "away"

            is_correct = pred_label == actual_label
            if is_correct:
                correct += 1
            total += 1

            all_probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
            all_outcomes.append(actual_vec)

            match_details.append({
                "tournament": tournament,
                "stage": m.stage,
                "home": m.home_team,
                "away": m.away_team,
                "score": f"{m.home_goals}-{m.away_goals}",
                "pred": pred_label,
                "actual": actual_label,
                "correct": is_correct,
                "home_win_pct": round(r.home_win_prob * 100, 1),
                "draw_pct": round(r.draw_prob * 100, 1),
                "away_win_pct": round(r.away_win_prob * 100, 1),
                "home_xg": r.home_expected_goals,
                "away_xg": r.away_expected_goals,
            })

    probs_arr = np.array(all_probs)
    outcomes_arr = np.array(all_outcomes)
    n = len(match_details)

    accuracy = correct / total if total > 0 else 0
    avg_brier = metrics.brier_score(probs_arr, outcomes_arr)
    avg_log_loss = metrics.log_loss(probs_arr, outcomes_arr)
    avg_rps = metrics.ranked_probability_score(probs_arr, outcomes_arr)
    ece, ece_bins = metrics.expected_calibration_error(probs_arr, outcomes_arr)

    # Per-tournament breakdown
    tournaments = {}
    for t_name in ("2014", "2018", "2022"):
        t_matches = [m for m in match_details if m["tournament"] == t_name]
        if not t_matches:
            continue
        t_probs = np.array([[m["home_win_pct"] / 100, m["draw_pct"] / 100, m["away_win_pct"] / 100] for m in t_matches])
        t_outcomes = np.array([[1, 0, 0] if m["actual"] == "home" else [0, 1, 0] if m["actual"] == "draw" else [0, 0, 1] for m in t_matches])
        t_correct = sum(1 for m in t_matches if m["correct"])
        tournaments[t_name] = {
            "matches": len(t_matches),
            "accuracy": round(t_correct / len(t_matches), 4),
            "brier": round(metrics.brier_score(t_probs, t_outcomes), 6),
            "log_loss": round(metrics.log_loss(t_probs, t_outcomes), 6),
            "rps": round(metrics.ranked_probability_score(t_probs, t_outcomes), 6),
        }

    # ── Print summary ──
    print("=" * 70)
    print("MATCH PREDICTION VALIDATION — ALL WORLD CUPS")
    print("=" * 70)

    print(f"\nTotal matches:     {n}")
    print(f"Accuracy:          {accuracy:.4f} ({correct}/{total})")
    print(f"Avg Brier Score:   {avg_brier:.6f}")
    print(f"Avg Log Loss:      {avg_log_loss:.6f}")
    print(f"Avg RPS:           {avg_rps:.6f}")
    print(f"ECE:               {ece:.6f}")

    print(f"\n{'Tournament':<12} {'Matches':>8} {'Accuracy':>10} {'Brier':>10} {'LogLoss':>10} {'RPS':>10}")
    print("-" * 60)
    for t_name in ("2014", "2018", "2022"):
        t = tournaments.get(t_name, {})
        print(f"{t_name:<12} {t.get('matches', 0):>8} {t.get('accuracy', 0):>10.4f} {t.get('brier', 0):>10.6f} {t.get('log_loss', 0):>10.6f} {t.get('rps', 0):>10.6f}")
    print(f"{'Total':<12} {n:>8} {accuracy:>10.4f} {avg_brier:>10.6f} {avg_log_loss:>10.6f} {avg_rps:>10.6f}")

    # Calibration curve
    print(f"\n\nCalibration Curve ({len(ece_bins)} bins):")
    print(f"{'Bin':<12} {'Count':>6} {'Confidence':>12} {'Accuracy':>10} {'Gap':>8}")
    print("-" * 50)
    for b in ece_bins:
        print(f"{b['bin_lower']:.1f}-{b['bin_upper']:.1f}    {b['count']:>6} {b['mean_confidence']:>12.4f} {b['mean_accuracy']:>10.4f} {b['gap']:>8.4f}")

    # Confusion-like breakdown by stage
    print(f"\n\nAccuracy by Stage:")
    stages = ["group", "round_of_16", "quarter_final", "semi_final", "final"]
    print(f"{'Stage':<20} {'Matches':>8} {'Correct':>8} {'Accuracy':>10}")
    print("-" * 46)
    for stage in stages:
        stage_matches = [m for m in match_details if m["stage"] == stage]
        if stage_matches:
            sc = sum(1 for m in stage_matches if m["correct"])
            print(f"{stage:<20} {len(stage_matches):>8} {sc:>8} {sc/len(stage_matches):>10.4f}")

    # Save data
    os.makedirs("docs", exist_ok=True)
    output = {
        "total_matches": n,
        "accuracy": accuracy,
        "brier": avg_brier,
        "log_loss": avg_log_loss,
        "rps": avg_rps,
        "ece": ece,
        "by_tournament": tournaments,
        "calibration_bins": ece_bins,
        "match_details": match_details[:20],  # first 20 for sample
    }
    with open("docs/match_validation_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n\nData saved to docs/match_validation_data.json")

    # Generate Markdown report
    lines = []
    lines.append("# Match Validation Report\n")
    lines.append("## Global Metrics\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Matches | {n} |")
    lines.append(f"| Accuracy | {accuracy:.4f} ({correct}/{total}) |")
    lines.append(f"| Brier Score | {avg_brier:.6f} |")
    lines.append(f"| Log Loss | {avg_log_loss:.6f} |")
    lines.append(f"| RPS | {avg_rps:.6f} |")
    lines.append(f"| ECE | {ece:.6f} |")
    lines.append("")
    lines.append("## By Tournament\n")
    lines.append("| Tournament | Matches | Accuracy | Brier | Log Loss | RPS |")
    lines.append("|-----------|--------|---------|------|---------|-----|")
    for t_name in ("2014", "2018", "2022"):
        t = tournaments.get(t_name, {})
        lines.append(f"| {t_name} | {t.get('matches', 0)} | {t.get('accuracy', 0):.4f} | {t.get('brier', 0):.6f} | {t.get('log_loss', 0):.6f} | {t.get('rps', 0):.6f} |")
    lines.append("")
    lines.append("## Calibration Curve\n")
    lines.append("| Bin | Count | Mean Confidence | Mean Accuracy | Gap |")
    lines.append("|-----|-------|---------------|-------------|-----|")
    for b in ece_bins:
        lines.append(f"| {b['bin_lower']:.1f}-{b['bin_upper']:.1f} | {b['count']} | {b['mean_confidence']:.4f} | {b['mean_accuracy']:.4f} | {b['gap']:.4f} |")
    lines.append("")
    lines.append("## By Stage\n")
    lines.append("| Stage | Accuracy |")
    lines.append("|-------|---------|")
    for stage in stages:
        stage_matches = [m for m in match_details if m["stage"] == stage]
        if stage_matches:
            sc = sum(1 for m in stage_matches if m["correct"])
            lines.append(f"| {stage} | {sc/len(stage_matches):.4f} |")
    lines.append("")

    report_text = "\n".join(lines)
    with open("docs/match_validation.md", "w", encoding="utf-8") as f:
        f.write(report_text)
    print("Report saved to docs/match_validation.md")


if __name__ == "__main__":
    main()
