from __future__ import annotations

import math


def _fmt_pct(v: float) -> str:
    return f"{v:+.1f}%" if abs(v) < 100 else f"{v:+.0f}%"


def _direction(v: float) -> str:
    return "subió" if v > 0 else "cayó"


def _adj(v: float) -> str:
    if abs(v) < 2:
        return "ligeramente"
    if abs(v) < 5:
        return "moderadamente"
    return "significativamente"


def generate_headline(insights: dict) -> str:
    contenders = insights.get("contenders", [])
    dark = insights.get("dark_horses", [])
    over = insights.get("overrated", [])
    under = insights.get("underrated", [])

    if contenders:
        top = contenders[0]["team_name"]
        return f"{top} lidera la carrera al título"
    if dark:
        return f"{dark[0]['team_name']} emerge como dark horse"
    return "Torneo en plena definición"


def generate_story(
    teams: list[dict],
    prev_teams: list[dict] | None = None,
) -> str:
    if not teams:
        return "No hay datos suficientes para generar una narrativa."

    top = max(teams, key=lambda t: t.get("win_prob", 0))
    parts = [
        f"{top['team_name']} es el favorito al título con {top['win_prob']:.1f}% de probabilidad de campeonato."
    ]

    if prev_teams:
        prev_map = {t["team_name"]: t for t in prev_teams}
        deltas = []
        for t in teams:
            if t["team_name"] in prev_map:
                delta = t["win_prob"] - prev_map[t["team_name"]]["win_prob"]
                if abs(delta) >= 0.5:
                    deltas.append((t["team_name"], delta, t["win_prob"]))
        deltas.sort(key=lambda x: abs(x[1]), reverse=True)
        if deltas:
            name, delta, _ = deltas[0]
            parts.append(
                f"{name} {_direction(delta)} sus probabilidades {_adj(delta)} ({_fmt_pct(delta)}) respecto a la simulación anterior."
            )
        if len(deltas) > 1:
            name, delta, _ = deltas[-1]
            if abs(delta) >= 1:
                parts.append(
                    f"Por otro lado, {name} {_direction(delta)} {_adj(abs(delta))} ({_fmt_pct(delta)})."
                )

    max_risk = max(teams, key=lambda t: abs(t.get("surprise_risk", 0) if isinstance(t.get("surprise_risk"), (int, float)) else 0))
    risk_val = max_risk.get("surprise_risk", 0)
    if isinstance(risk_val, (int, float)) and risk_val > 0.15:
        parts.append(f"{max_risk['team_name']} presenta alta sorpresividad ({risk_val:.0%}).")

    return " ".join(parts)


def generate_team_story(team: dict) -> str:
    name = team.get("team_name", "Unknown")
    win = team.get("win_prob", 0)
    elo = team.get("elo_score", 1500)
    rank = team.get("fifa_rank")
    xg_for = team.get("xg_for")
    xg_against = team.get("xg_against")

    strengths = []
    weaknesses = []

    if elo > 1900:
        strengths.append("alto nivel de Elo")
    elif elo < 1600:
        weaknesses.append("Elo por debajo del promedio")

    if win > 5:
        strengths.append(f"sólida probabilidad de campeonato ({win:.1f}%)")
    elif win < 0.5:
        weaknesses.append("baja probabilidad de avanzar en el torneo")

    if xg_for is not None and xg_for > 1.5:
        strengths.append("potencia ofensiva destacada")
    elif xg_for is not None and xg_for < 0.8:
        weaknesses.append("producción ofensiva limitada")

    if xg_against is not None and xg_against < 0.8:
        strengths.append("solvencia defensiva")
    elif xg_against is not None and xg_against > 1.5:
        weaknesses.append("vulnerabilidad defensiva")

    if rank is not None and rank < 10:
        strengths.append(f"ranking FIFA top 10 (#{rank})")

    lines = [f"{name} "]
    if strengths and weaknesses:
        lines[0] += f"destaca por {' y '.join(strengths)}, aunque {' y '.join(weaknesses)}."
    elif strengths:
        lines[0] += f"se distingue por {' y '.join(strengths)}."
    elif weaknesses:
        lines[0] += f"presenta desafíos: {' y '.join(weaknesses)}."
    else:
        lines[0] += "presenta un perfil equilibrado sin fortalezas ni debilidades claras."

    return " ".join(lines)


def generate_risks(insights: dict, teams: list[dict]) -> list[str]:
    risks = []
    over = insights.get("overrated", [])
    for o in over[:3]:
        risks.append(f"{o['team_name']} podría no cumplir con las expectativas (Elo alto, probabilidad baja).")
    if teams:
        volatile = [t for t in teams if abs(t.get("surprise_risk", 0) if isinstance(t.get("surprise_risk"), (int, float)) else 0) > 0.2]
        for v in volatile[:2]:
            risks.append(f"{v['team_name']} es altamente impredecible.")
    return risks


def generate_opportunities(insights: dict) -> list[str]:
    opps = []
    dark = insights.get("dark_horses", [])
    for d in dark[:3]:
        opps.append(f"{d['team_name']} tiene potencial de sorpresa (ranking medio, alta probabilidad relativa).")
    under = insights.get("underrated", [])
    for u in under[:2]:
        opps.append(f"{u['team_name']} está infravalorado por su ranking pero tiene altas probabilidades.")
    return opps


def generate_feed_events(
    teams: list[dict],
    prev_teams: list[dict] | None = None,
    insights: dict | None = None,
) -> list[dict]:
    events = []
    if prev_teams:
        prev_map = {t["team_name"]: t for t in prev_teams}
        for t in teams:
            if t["team_name"] in prev_map:
                dp = t["win_prob"] - prev_map[t["team_name"]]["win_prob"]
                if abs(dp) >= 0.5:
                    events.append({
                        "headline": f"{t['team_name']} {_fmt_pct(dp)}",
                        "detail": f"{t['team_name']} {_direction(dp)} sus probabilidades de campeonato {_adj(abs(dp))} ({_fmt_pct(dp)}).",
                        "delta": round(dp, 1),
                        "direction": "up" if dp > 0 else "down",
                    })
        # top entries change
        if len(teams) >= 5 and prev_teams:
            curr_top5 = {t["team_name"] for t in teams[:5]}
            prev_top5 = {t["team_name"] for t in prev_teams[:5]}
            entered = curr_top5 - prev_top5
            left = prev_top5 - curr_top5
            for e in entered:
                events.append({
                    "headline": f"{e} entra al Top 5",
                    "detail": f"{e} ingresó al Top 5 de candidatos al título.",
                    "delta": None,
                    "direction": "up",
                })
            for l in left:
                events.append({
                    "headline": f"{l} sale del Top 5",
                    "detail": f"{l} cayó fuera del Top 5 de candidatos.",
                    "delta": None,
                    "direction": "down",
                })

    if insights:
        dark = insights.get("dark_horses", [])
        for d in dark[:2]:
            events.append({
                "headline": f"{d['team_name']} es dark horse",
                "detail": f"{d['team_name']} emerge como candidato sorpresa con {d['win_prob']:.1f}% de probabilidad.",
                "delta": None,
                "direction": "up",
            })
        over = insights.get("overrated", [])
        for o in over[:2]:
            events.append({
                "headline": f"{o['team_name']} sobrevalorado",
                "detail": f"{o['team_name']} tiene Elo alto ({o['elo_score']}) pero baja probabilidad ({o['win_prob']:.1f}%).",
                "delta": None,
                "direction": "down",
            })

    events.sort(key=lambda e: abs(e["delta"]) if e["delta"] is not None else 0, reverse=True)
    return events
