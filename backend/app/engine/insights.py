from __future__ import annotations

import numpy as np


def compute_insights(teams: list[dict]) -> dict:
    """
    Derive contenders, dark horses, overrated, and underrated from
    a list of team dicts with at minimum:
      - team_name
      - elo_score (int)
      - win_prob (float, percentage e.g. 12.5)
    """
    if not teams:
        return {"contenders": [], "dark_horses": [], "overrated": [], "underrated": []}

    arr = np.array([(t["elo_score"], t["win_prob"]) for t in teams])
    elos = arr[:, 0]
    probs = arr[:, 1]

    elo_mean, elo_std = float(np.mean(elos)), float(np.std(elos)) or 1.0
    prob_mean, prob_std = float(np.mean(probs)), float(np.std(probs)) or 1.0

    contenders = []
    dark_horses = []
    overrated = []
    underrated = []

    for t in teams:
        elo_z = (t["elo_score"] - elo_mean) / elo_std
        prob_z = (t["win_prob"] - prob_mean) / prob_std

        info = {
            "team_name": t["team_name"],
            "elo_score": t["elo_score"],
            "win_prob": t["win_prob"],
            "z_score_elo": round(elo_z, 2),
            "z_score_prob": round(prob_z, 2),
        }

        # Contenders: top win prob
        if prob_z > 1.0:
            contenders.append(info)

        # Dark horses: mid elo (z -1..+1) but above-avg win prob
        if -1.0 <= elo_z <= 1.0 and prob_z > 0.5:
            dark_horses.append(info)

        # Overrated: elo z > 1 but prob z < 0
        if elo_z > 1.0 and prob_z < 0:
            overrated.append(info)

        # Underrated: elo z < -1 but prob z > 0
        if elo_z < -1.0 and prob_z > 0:
            underrated.append(info)

    def sort_key(k: str, reverse: bool = True):
        return lambda x: x[k]

    contenders.sort(key=sort_key("win_prob"), reverse=True)
    dark_horses.sort(key=sort_key("win_prob"), reverse=True)
    overrated.sort(key=sort_key("elo_score"), reverse=True)
    underrated.sort(key=sort_key("elo_score"))

    return {
        "contenders": contenders[:8],
        "dark_horses": dark_horses[:6],
        "overrated": overrated[:6],
        "underrated": underrated[:6],
    }
