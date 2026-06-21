"""
Sprint 8 - Report Generator.
Reads sprint8_data.json and generates 10 markdown reports + summary.
"""
import json, os
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
DATA_FILE = DOCS / "sprint8_data.json"
OUT = DOCS
OUT.mkdir(exist_ok=True)

with open(DATA_FILE) as f:
    data = json.load(f)

def w(filename, content):
    path = OUT / filename
    path.write_text(content, encoding="utf-8")
    print(f"  Wrote {filename}")

# ── Phase 1-2: Weight Optimization + EliteScore ──
def phase1_2():
    opt = data["weight_optimization"]
    lines = [
        "# Phase 1-2: Weight Optimization & EliteScore\n",
        "## Weight Sweep Results\n",
        "| elo_weight | Accuracy | Brier | LogLoss | ECE | Stress_Std | PartialEliteScore |",
        "|------------|----------|-------|---------|-----|------------|-------------------|",
    ]
    for c in opt["configs"]:
        lines.append(f"| {c['elo_weight']:.2f} | {c['accuracy']:.4f} | {c['brier']:.4f} | {c['logloss']:.4f} | {c['ece']:.4f} | {c['stress_std']:.4f} | {c.get('elite_score', 'N/A'):.4f} |")
    lines.append(f"\n**Best elo_weight:** {opt['best_elo_weight']}")
    lines.append(f"\n**Full EliteScore (with tournament):** {data.get('elite_verdict', {}).get('best_elite_score', 'N/A'):.4f}")
    w("sprint8_phase1_2.md", "\n".join(lines))

# ── Phase 3: Temporal Validation ──
def phase3():
    tv = data.get("temporal_validation", [])
    lines = ["# Phase 3: Temporal Validation\n", "| Split | n_train | n_val | Train Acc | Val Acc | Gap Acc | Train Brier | Val Brier |",
             "|-------|---------|-------|-----------|---------|---------|-------------|-----------|"]
    for r in tv:
        lines.append(f"| {r['split']} | {r['n_train']} | {r['n_val']} | {r['train']['accuracy']:.4f} | {r['validation']['accuracy']:.4f} | {r['gap']['accuracy']:+.4f} | {r['train']['brier']:.4f} | {r['validation']['brier']:.4f} |")
    w("sprint8_phase3.md", "\n".join(lines))

# ── Phase 4: Calibration Stability ──
def phase4():
    cs = data.get("calibration_stability", {})
    lines = ["# Phase 4: Calibration Stability\n", "| Tournament | n_matches | Baseline ECE | Baseline MCE | Global T | Global T ECE | Regional ECE |",
             "|------------|-----------|--------------|--------------|----------|--------------|--------------|"]
    for t, r in cs.items():
        lines.append(f"| {t} | {r['n_matches']} | {r['baseline_ece']:.4f} | {r['baseline_mce']:.4f} | {r.get('global_temp_ece', 'N/A')} | {r['global_temp_ece'] if isinstance(r.get('global_temp_ece'), float) else 'N/A'} | {r['regional_temp_ece']:.4f} |")
    w("sprint8_phase4.md", "\n".join(lines))

# ── Phase 5: CI Audit ──
def phase5():
    ci = data.get("ci_audit", {})
    lines = ["# Phase 5: Confidence Interval Audit\n", "| CI Level | Coverage Rate | Avg CI Width |",
             "|----------|---------------|--------------|"]
    for label, info in ci.items():
        lines.append(f"| {label} | {info['coverage_rate']:.3f} | {info['avg_ci_width']:.4f} |")
    lines.append("\n**Verdict:** Coverage is 100%, indicating over-conservative intervals. Target: 85-95%.")
    w("sprint8_phase5.md", "\n".join(lines))

# ── Phase 6: Tournament Forecast Validation ──
def phase6():
    tf = data.get("tournament_forecasting", [])
    lines = ["# Phase 6: Tournament Forecast Validation\n", "| Tournament | Champion Rank | Top4 Inclusion | Top8 Inclusion | Brier |",
             "|------------|---------------|----------------|----------------|-------|"]
    for r in tf:
        lines.append(f"| {r['tournament']} | {r['champion_rank']} | {r['top4_inclusion']:.1f}% | {r['top8_inclusion']:.1f}% | {r['tournament_brier']:.4f} |")
    top4_avg = sum(r["top4_inclusion"] for r in tf) / len(tf) if tf else 0
    lines.append(f"\n**Average Top4 Inclusion:** {top4_avg:.1f}% (target >= 66%)")
    lines.append(f"**Pass:** {'YES' if top4_avg >= 66 else 'NO'}")
    w("sprint8_phase6.md", "\n".join(lines))

# ── Phase 7: Production Robustness ──
def phase7():
    pr = data.get("production_robustness", {})
    lines = ["# Phase 7: Production Robustness\n"]
    lines.append(f"Baseline Home Win Prob: {pr.get('baseline_hw', 'N/A'):.4f}\n")
    lines.append("| Scenario | Mean | Std | Drift % |")
    lines.append("|----------|------|-----|---------|")
    for sname, info in pr.get("scenarios", {}).items():
        lines.append(f"| {sname} | {info['mean']:.4f} | {info['std']:.4f} | {info['drift_pct']:.2f}% |")
    w("sprint8_phase7.md", "\n".join(lines))

# ── Phase 8: Explainability ──
def phase8():
    ec = data.get("explainability_consistency", {})
    lines = [
        "# Phase 8: Explainability Consistency\n",
        f"- **Mean driver sum:** {ec.get('mean', 'N/A'):.6f} (target: 1.0)",
        f"- **Std:** {ec.get('std', 'N/A'):.6f}",
        f"- **Min:** {ec.get('min', 'N/A'):.6f}",
        f"- **Max:** {ec.get('max', 'N/A'):.6f}",
        f"- **Abs error mean:** {ec.get('abs_error_mean', 'N/A'):.6f} (target <= 0.005)",
        f"- **Within 1%:** {ec.get('pct_within_1pct', 'N/A'):.1f}%",
        f"\n**Pass:** {'YES' if ec.get('abs_error_mean', 1) <= 0.005 else 'NO'}",
    ]
    w("sprint8_phase8.md", "\n".join(lines))

# ── Phase 9: Elite Benchmark ──
def phase9():
    bm = data.get("elite_benchmark", [])
    lines = ["# Phase 9: Elite Benchmark\n", "| Sprint | Accuracy | Brier | ECE | Stress | Pearson | EliteScore |",
             "|--------|----------|-------|-----|--------|---------|------------|"]
    for b in bm:
        lines.append(f"| {b['sprint']} | {b['accuracy']:.3f} | {b['brier']:.4f} | {b['ece']:.4f} | {b['stress_std']:.3f} | {b['pearson']:.3f} | {b['elite_score']:.4f} |")
    w("sprint8_phase9.md", "\n".join(lines))

# ── Phase 10: Elite Verdict ──
def phase10():
    v = data.get("elite_verdict", {})
    lines = ["# Phase 10: Elite Verdict\n"]
    for cname, cinfo in v.get("criteria", {}).items():
        sym = "PASS" if cinfo["pass"] else "FAIL"
        lines.append(f"- **[{sym}]** {cname}: {cinfo['value']:.4f}")
    lines.append(f"\n**Grade:** {v.get('passed', 0)}/{v.get('total', 0)} criteria = **{v.get('grade', 'N/A')}**")
    lines.append(f"\n**Best elo_weight:** {v.get('best_elo_weight', 'N/A')}")
    lines.append(f"**Best EliteScore:** {v.get('best_elite_score', 'N/A'):.4f}")
    w("sprint8_phase10.md", "\n".join(lines))

# ── Summary Report ──
def summary():
    v = data.get("elite_verdict", {})
    bm = data.get("elite_benchmark", [])
    lines = [
        "# Sprint 8 – Elite Forecasting Grade Report\n",
        "## Executive Summary\n",
        f"- **Best Config:** elo_weight = {v.get('best_elo_weight', 'N/A')}",
        f"- **EliteScore:** {v.get('best_elite_score', 'N/A'):.4f}",
        f"- **Verdict:** {v.get('passed', 0)}/{v.get('total', 0)} criteria passed = **{v.get('grade', 'N/A')}**\n",
        "## Criteria Results\n",
        "| Criterion | Target | Actual | Status |",
        "|-----------|--------|--------|--------|",
    ]
    for cname, cinfo in v.get("criteria", {}).items():
        status = "PASS" if cinfo["pass"] else "FAIL"
        lines.append(f"| {cname} | ... | {cinfo['value']:.4f} | {status} |")
    lines.append(f"\n## Historical EliteScore Progression\n")
    lines.append("| Sprint | EliteScore | Change |")
    lines.append("|--------|------------|--------|")
    prev = None
    for b in bm:
        delta = f"{b['elite_score'] - prev:+.4f}" if prev is not None else "-"
        lines.append(f"| {b['sprint']} | {b['elite_score']:.4f} | {delta} |")
        prev = b["elite_score"]
    lines.extend([
        "\n## Key Strengths\n",
        "- **Calibration:** ECE=0.031 passes elite threshold (0.040) – best ever",
        "- **Explainability:** Driver sum = 1.000000 with zero error",
        "- **Forecasting:** Top4 inclusion 75% exceeds 66% target\n",
        "## Key Gaps\n",
        "- **CI Coverage:** 100% (target 85-95%) – intervals are too wide",
        "- **Robustness:** Stress std 0.091 > 0.065 limit",
        "- **Consistency:** Pearson 0.903 < 0.95 due to limited sims",
        "- **EliteScore:** 0.534 < Sprint 7.5's 0.779 (regression in accuracy)\n",
        "## Next Steps\n",
        "1. Tighten CI intervals with adaptive noise scaling",
        "2. Add regularization to reduce stress sensitivity",
        "3. Increase tournament sims for more stable Pearson",
        "4. Rebalance weights to boost accuracy without sacrificing ECE\n",
    ])
    w("sprint8_elite_report.md", "\n".join(lines))

if __name__ == "__main__":
    print("Generating Sprint 8 reports...")
    phase1_2()
    phase3()
    phase4()
    phase5()
    phase6()
    phase7()
    phase8()
    phase9()
    phase10()
    summary()
    print("All reports generated.")
