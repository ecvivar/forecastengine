"""
Sprint 4A — FASE 4: Probabilistic Calibration.

Implements Platt Scaling, Isotonic Regression, and Temperature Scaling
for 3-outcome football predictions. Compares before/after metrics on 192 matches.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from scipy.optimize import minimize, fminbound
from app.data.historical_matches import ALL_HISTORICAL_MATCHES
from app.domain.entities import PredictionConfig, TeamEntity
from app.engine.match_prediction import MatchPredictionEngine
from app.validation.calibration_metrics import CalibrationMetrics
from app.validation.backtesting import BacktestingEngine

DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")
os.makedirs(DOCS, exist_ok=True)


def build_dataset():
    """Build prediction/outcome arrays over 192 historical matches."""
    config = PredictionConfig()
    engine = MatchPredictionEngine(config=config)
    bt = BacktestingEngine(config=config)
    team_data = bt._extract_team_data(ALL_HISTORICAL_MATCHES)
    team_entities = {name: bt._build_team_entity(name, d) for name, d in team_data.items()}

    probs, outcomes = [], []
    for m in ALL_HISTORICAL_MATCHES:
        home = team_entities.get(m.home_team)
        away = team_entities.get(m.away_team)
        if not home or not away:
            continue
        r = engine.predict_full(home, away, home_advantage=True)
        probs.append([r.home_win_prob, r.draw_prob, r.away_win_prob])
        if m.home_goals > m.away_goals:
            outcomes.append([1, 0, 0])
        elif m.home_goals == m.away_goals:
            outcomes.append([0, 1, 0])
        else:
            outcomes.append([0, 0, 1])
    return np.array(probs), np.array(outcomes)


def platt_scaling(probs, outcomes):
    """Platt scaling using logistic regression on logits."""
    # Use home_win confidence (max prob) as the scalar input
    max_probs = np.max(probs, axis=1)
    y = (np.argmax(probs, axis=1) == np.argmax(outcomes, axis=1)).astype(float)

    # Optimize [a, b] for logit scaling: P(y=1|x) = 1/(1+exp(a*logit(x)+b))
    logits = np.log(np.clip(max_probs, 1e-15, 1 - 1e-15) / (1 - np.clip(max_probs, 1e-15, 1 - 1e-15)))

    def platt_loss(params):
        a, b = params
        scaled = 1.0 / (1.0 + np.exp(-(a * logits + b)))
        scaled = np.clip(scaled, 1e-15, 1 - 1e-15)
        return -np.mean(y * np.log(scaled) + (1 - y) * np.log(1 - scaled))

    result = minimize(platt_loss, [1.0, 0.0], method='Nelder-Mead')
    a, b = result.x

    # Apply Platt scaling to the original 3-class probabilities
    scaled = probs.copy()
    for i in range(len(scaled)):
        # Scale confidence: max prob gets the adjusted confidence, then renormalize
        pred_class = np.argmax(scaled[i])
        conf = max_probs[i]
        logit = np.log(max(1e-15, conf / (1 - conf)))
        new_conf = 1.0 / (1.0 + np.exp(-(a * logit + b)))
        # Distribute the confidence adjustment to keep ratios
        conf_ratio = new_conf / max(conf, 1e-15)
        scaled[i] = scaled[i] * conf_ratio
        scaled[i] = np.clip(scaled[i], 1e-15, 1 - 1e-15)
        scaled[i] /= scaled[i].sum()
    return scaled, {"a": round(a, 4), "b": round(b, 4)}


def isotonic_regression(probs, outcomes):
    """Simple bin-based isotonic regression."""
    max_probs = np.max(probs, axis=1)
    y_correct = (np.argmax(probs, axis=1) == np.argmax(outcomes, axis=1)).astype(float)

    # Sort by confidence
    order = np.argsort(max_probs)
    sorted_p = max_probs[order]
    sorted_y = y_correct[order]
    n = len(sorted_p)

    # PAVA (pool adjacent violators) - simplified version
    # Group into bins and enforce monotonicity
    bins = np.linspace(0, 1, 21)  # 20 bins
    bin_means = np.zeros(20)
    bin_counts = np.zeros(20)

    for i in range(20):
        lo, hi = bins[i], bins[i + 1]
        if i == 19:
            mask = (sorted_p >= lo) & (sorted_p <= hi)
        else:
            mask = (sorted_p >= lo) & (sorted_p < hi)
        cnt = int(np.sum(mask))
        bin_counts[i] = cnt
        if cnt > 0:
            bin_means[i] = float(np.mean(sorted_y[mask]))
        else:
            bin_means[i] = bins[i] + 0.025  # midpoint

    # Enforce monotonicity: ensure non-decreasing
    for i in range(1, 20):
        if bin_counts[i] > 0 and bin_counts[i-1] > 0:
            if bin_means[i] < bin_means[i-1]:
                avg = (bin_means[i] * bin_counts[i] + bin_means[i-1] * bin_counts[i-1]) / (bin_counts[i] + bin_counts[i-1])
                bin_means[i-1] = bin_means[i] = avg

    # Apply calibration
    calibrated = probs.copy()
    for i in range(len(calibrated)):
        conf = max_probs[i]
        bin_idx = min(19, int(conf * 20))
        cal_conf = bin_means[bin_idx]
        conf_ratio = max(cal_conf / max(conf, 1e-15), 0.01)
        calibrated[i] = calibrated[i] * conf_ratio
        calibrated[i] = np.clip(calibrated[i], 1e-15, 1 - 1e-15)
        calibrated[i] /= calibrated[i].sum()
    return calibrated, {}


def temperature_scaling(probs, outcomes):
    """Temperature scaling: T parameter scales logits."""
    logits = np.log(np.clip(probs, 1e-15, 1 - 1e-15))

    def nll(T):
        scaled = np.exp(logits / T)
        scaled /= scaled.sum(axis=1, keepdims=True)
        return -np.mean(np.sum(outcomes * np.log(np.clip(scaled, 1e-15, 1)), axis=1))

    result = fminbound(lambda t: nll(max(t, 0.01)), 0.1, 10.0, full_output=True)
    T = result[0]
    scaled = np.exp(logits / T)
    scaled /= scaled.sum(axis=1, keepdims=True)
    return scaled, {"T": round(T, 4)}


metrics = CalibrationMetrics()
probs, outcomes = build_dataset()

print(f"Dataset: {len(probs)} matches\n")

# Before calibration
brier_before = metrics.brier_score(probs, outcomes)
logloss_before = metrics.log_loss(probs, outcomes)
rps_before = metrics.ranked_probability_score(probs, outcomes)
ece_before, _ = metrics.expected_calibration_error(probs, outcomes)
print("Before calibration:")
print(f"  Brier:    {brier_before:.6f}")
print(f"  LogLoss:  {logloss_before:.6f}")
print(f"  RPS:      {rps_before:.6f}")
print(f"  ECE:      {ece_before:.6f}")

# Platt Scaling
platt_probs, platt_params = platt_scaling(probs, outcomes)
brier_platt = metrics.brier_score(platt_probs, outcomes)
logloss_platt = metrics.log_loss(platt_probs, outcomes)
rps_platt = metrics.ranked_probability_score(platt_probs, outcomes)
ece_platt, _ = metrics.expected_calibration_error(platt_probs, outcomes)
print(f"\nPlatt Scaling (a={platt_params.get('a','?')}, b={platt_params.get('b','?')}):")
print(f"  Brier:    {brier_platt:.6f}  (delta={brier_platt - brier_before:+.6f})")
print(f"  LogLoss:  {logloss_platt:.6f}  (delta={logloss_platt - logloss_before:+.6f})")
print(f"  RPS:      {rps_platt:.6f}  (delta={rps_platt - rps_before:+.6f})")
print(f"  ECE:      {ece_platt:.6f}  (delta={ece_platt - ece_before:+.6f})")

# Isotonic Regression
iso_probs, _ = isotonic_regression(probs, outcomes)
brier_iso = metrics.brier_score(iso_probs, outcomes)
logloss_iso = metrics.log_loss(iso_probs, outcomes)
rps_iso = metrics.ranked_probability_score(iso_probs, outcomes)
ece_iso, _ = metrics.expected_calibration_error(iso_probs, outcomes)
print(f"\nIsotonic Regression:")
print(f"  Brier:    {brier_iso:.6f}  (delta={brier_iso - brier_before:+.6f})")
print(f"  LogLoss:  {logloss_iso:.6f}  (delta={logloss_iso - logloss_before:+.6f})")
print(f"  RPS:      {rps_iso:.6f}  (delta={rps_iso - rps_before:+.6f})")
print(f"  ECE:      {ece_iso:.6f}  (delta={ece_iso - ece_before:+.6f})")

# Temperature Scaling
temp_probs, temp_params = temperature_scaling(probs, outcomes)
brier_temp = metrics.brier_score(temp_probs, outcomes)
logloss_temp = metrics.log_loss(temp_probs, outcomes)
rps_temp = metrics.ranked_probability_score(temp_probs, outcomes)
ece_temp, _ = metrics.expected_calibration_error(temp_probs, outcomes)
print(f"\nTemperature Scaling (T={temp_params.get('T','?')}):")
print(f"  Brier:    {brier_temp:.6f}  (delta={brier_temp - brier_before:+.6f})")
print(f"  LogLoss:  {logloss_temp:.6f}  (delta={logloss_temp - logloss_before:+.6f})")
print(f"  RPS:      {rps_temp:.6f}  (delta={rps_temp - rps_before:+.6f})")
print(f"  ECE:      {ece_temp:.6f}  (delta={ece_temp - ece_before:+.6f})")

# Save results
comparison = {
    "Before": {
        "brier": round(brier_before, 6),
        "log_loss": round(logloss_before, 6),
        "rps": round(rps_before, 6),
        "ece": round(ece_before, 6),
    },
    "PlattScaling": {
        "brier": round(brier_platt, 6),
        "log_loss": round(logloss_platt, 6),
        "rps": round(rps_platt, 6),
        "ece": round(ece_platt, 6),
        "params": platt_params,
    },
    "IsotonicRegression": {
        "brier": round(brier_iso, 6),
        "log_loss": round(logloss_iso, 6),
        "rps": round(rps_iso, 6),
        "ece": round(ece_iso, 6),
    },
    "TemperatureScaling": {
        "brier": round(brier_temp, 6),
        "log_loss": round(logloss_temp, 6),
        "rps": round(rps_temp, 6),
        "ece": round(ece_temp, 6),
        "params": temp_params,
    },
}

with open(os.path.join(DOCS, "calibration_comparison_data.json"), "w") as f:
    json.dump(comparison, f, indent=2)
print(f"\nSaved to docs/calibration_comparison_data.json")
