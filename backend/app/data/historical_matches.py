"""
Historical World Cup matches for calibration (2014, 2018, 2022).
IGF values in 0-100 scale. Elo at tournament time. Includes confederation info.
"""

from app.domain.calibration import HistoricalMatchData

# Confederation lookup for bias analysis
CONFEDERATIONS: dict[str, str] = {
    # UEFA
    "Germany": "UEFA", "Spain": "UEFA", "Netherlands": "UEFA", "Italy": "UEFA",
    "England": "UEFA", "Portugal": "UEFA", "France": "UEFA", "Belgium": "UEFA",
    "Croatia": "UEFA", "Switzerland": "UEFA", "Russia": "UEFA", "Greece": "UEFA",
    "Bosnia": "UEFA", "Denmark": "UEFA", "Sweden": "UEFA", "Poland": "UEFA",
    "Serbia": "UEFA", "Iceland": "UEFA", "Wales": "UEFA", "Slovakia": "UEFA",
    "Slovenia": "UEFA", "Ukraine": "UEFA", "Scotland": "UEFA", "Turkey": "UEFA",
    "Austria": "UEFA", "Czech Republic": "UEFA", "Hungary": "UEFA", "Albania": "UEFA",
    "Northern Ireland": "UEFA",
    # CONMEBOL
    "Brazil": "CONMEBOL", "Argentina": "CONMEBOL", "Uruguay": "CONMEBOL",
    "Colombia": "CONMEBOL", "Chile": "CONMEBOL", "Ecuador": "CONMEBOL",
    "Peru": "CONMEBOL", "Paraguay": "CONMEBOL", "Venezuela": "CONMEBOL",
    # CONCACAF
    "Mexico": "CONCACAF", "USA": "CONCACAF", "Costa Rica": "CONCACAF",
    "Canada": "CONCACAF", "Honduras": "CONCACAF", "Jamaica": "CONCACAF",
    "Panama": "CONCACAF", "Trinidad and Tobago": "CONCACAF",
    # CAF
    "Nigeria": "CAF", "Ghana": "CAF", "Ivory Coast": "CAF", "Cameroon": "CAF",
    "Algeria": "CAF", "Morocco": "CAF", "Senegal": "CAF", "Tunisia": "CAF",
    "Egypt": "CAF", "South Africa": "CAF", "Burkina Faso": "CAF",
    "Cape Verde": "CAF", "DR Congo": "CAF", "Mali": "CAF", "Togo": "CAF",
    # AFC
    "Japan": "AFC", "South Korea": "AFC", "Australia": "AFC",
    "Saudi Arabia": "AFC", "Iran": "AFC", "Qatar": "AFC",
    "Iraq": "AFC", "UAE": "AFC", "Oman": "AFC", "China": "AFC",
    "North Korea": "AFC", "Kuwait": "AFC",
    # OFC
    "New Zealand": "OFC",
}


def _m(
    tournament: str, stage: str,
    home: str, away: str,
    hg: int, ag: int,
    helo: int, aelo: int,
    higf: float, aigf: float,
    hp: int | None = None, ap: int | None = None,
) -> HistoricalMatchData:
    return HistoricalMatchData(
        tournament=tournament, stage=stage,
        home_team=home, away_team=away,
        home_goals=hg, away_goals=ag,
        home_elo=helo, away_elo=aelo,
        home_igf=higf, away_igf=aigf,
        home_penalties=hp, away_penalties=ap,
        home_confederation=CONFEDERATIONS.get(home, ""),
        away_confederation=CONFEDERATIONS.get(away, ""),
    )


# ============================================================
# 2014 World Cup (Brazil) – 64 matches total
# ============================================================
MATCHES_2014: list[HistoricalMatchData] = [
    # Group A
    _m("2014", "group", "Brazil", "Croatia", 3, 1, 2050, 1750, 85, 55),
    _m("2014", "group", "Mexico", "Cameroon", 1, 0, 1750, 1650, 55, 45),
    _m("2014", "group", "Brazil", "Mexico", 0, 0, 2050, 1750, 85, 55),
    _m("2014", "group", "Cameroon", "Croatia", 0, 4, 1650, 1750, 45, 55),
    _m("2014", "group", "Cameroon", "Brazil", 1, 4, 1650, 2050, 45, 85),
    _m("2014", "group", "Croatia", "Mexico", 1, 3, 1750, 1750, 55, 55),
    # Group B
    _m("2014", "group", "Spain", "Netherlands", 1, 5, 2000, 1950, 80, 75),
    _m("2014", "group", "Chile", "Australia", 3, 1, 1800, 1600, 60, 40),
    _m("2014", "group", "Spain", "Chile", 0, 2, 2000, 1800, 80, 60),
    _m("2014", "group", "Australia", "Netherlands", 2, 3, 1600, 1950, 40, 75),
    _m("2014", "group", "Australia", "Spain", 0, 3, 1600, 2000, 40, 80),
    _m("2014", "group", "Netherlands", "Chile", 2, 0, 1950, 1800, 75, 60),
    # Group C
    _m("2014", "group", "Colombia", "Greece", 3, 0, 1900, 1650, 70, 45),
    _m("2014", "group", "Ivory Coast", "Japan", 2, 1, 1750, 1650, 55, 45),
    _m("2014", "group", "Colombia", "Ivory Coast", 2, 1, 1900, 1750, 70, 55),
    _m("2014", "group", "Japan", "Greece", 0, 0, 1650, 1650, 45, 45),
    _m("2014", "group", "Japan", "Colombia", 1, 4, 1650, 1900, 45, 70),
    _m("2014", "group", "Greece", "Ivory Coast", 2, 1, 1650, 1750, 45, 55),
    # Group D
    _m("2014", "group", "Uruguay", "Costa Rica", 1, 3, 1800, 1600, 60, 40),
    _m("2014", "group", "England", "Italy", 1, 2, 1900, 1850, 70, 65),
    _m("2014", "group", "Uruguay", "England", 2, 1, 1800, 1900, 60, 70),
    _m("2014", "group", "Italy", "Costa Rica", 0, 1, 1850, 1600, 65, 40),
    _m("2014", "group", "Italy", "Uruguay", 0, 1, 1850, 1800, 65, 60),
    _m("2014", "group", "Costa Rica", "England", 0, 0, 1600, 1900, 40, 70),
    # Group E
    _m("2014", "group", "Switzerland", "Ecuador", 2, 1, 1750, 1700, 55, 50),
    _m("2014", "group", "France", "Honduras", 3, 0, 1850, 1550, 65, 35),
    _m("2014", "group", "Switzerland", "France", 2, 5, 1750, 1850, 55, 65),
    _m("2014", "group", "Honduras", "Ecuador", 1, 2, 1550, 1700, 35, 50),
    _m("2014", "group", "Honduras", "Switzerland", 0, 3, 1550, 1750, 35, 55),
    _m("2014", "group", "Ecuador", "France", 0, 0, 1700, 1850, 50, 65),
    # Group F
    _m("2014", "group", "Argentina", "Bosnia", 2, 1, 2000, 1700, 80, 50),
    _m("2014", "group", "Iran", "Nigeria", 0, 0, 1550, 1650, 35, 45),
    _m("2014", "group", "Argentina", "Iran", 1, 0, 2000, 1550, 80, 35),
    _m("2014", "group", "Nigeria", "Bosnia", 1, 0, 1650, 1700, 45, 50),
    _m("2014", "group", "Nigeria", "Argentina", 2, 3, 1650, 2000, 45, 80),
    _m("2014", "group", "Bosnia", "Iran", 3, 1, 1700, 1550, 50, 35),
    # Group G
    _m("2014", "group", "Germany", "Portugal", 4, 0, 2100, 1850, 90, 65),
    _m("2014", "group", "Ghana", "USA", 1, 2, 1700, 1700, 50, 50),
    _m("2014", "group", "Germany", "Ghana", 2, 2, 2100, 1700, 90, 50),
    _m("2014", "group", "USA", "Portugal", 2, 2, 1700, 1850, 50, 65),
    _m("2014", "group", "USA", "Germany", 0, 1, 1700, 2100, 50, 90),
    _m("2014", "group", "Portugal", "Ghana", 2, 1, 1850, 1700, 65, 50),
    # Group H
    _m("2014", "group", "Belgium", "Algeria", 2, 1, 1850, 1700, 65, 50),
    _m("2014", "group", "Russia", "South Korea", 1, 1, 1700, 1650, 50, 45),
    _m("2014", "group", "Belgium", "Russia", 1, 0, 1850, 1700, 65, 50),
    _m("2014", "group", "South Korea", "Algeria", 2, 4, 1650, 1700, 45, 50),
    _m("2014", "group", "South Korea", "Belgium", 0, 1, 1650, 1850, 45, 65),
    _m("2014", "group", "Algeria", "Russia", 1, 1, 1700, 1700, 50, 50),
    # Round of 16 (8 matches)
    _m("2014", "round_of_16", "Brazil", "Chile", 1, 1, 2050, 1800, 85, 60, 3, 2),
    _m("2014", "round_of_16", "Netherlands", "Mexico", 2, 1, 1950, 1750, 75, 55),
    _m("2014", "round_of_16", "Germany", "Algeria", 2, 1, 2100, 1600, 90, 40),
    _m("2014", "round_of_16", "Argentina", "Switzerland", 1, 0, 2000, 1750, 80, 55),
    _m("2014", "round_of_16", "Belgium", "USA", 2, 1, 1850, 1700, 65, 50),
    _m("2014", "round_of_16", "Colombia", "Uruguay", 2, 0, 1900, 1800, 70, 60),
    _m("2014", "round_of_16", "France", "Nigeria", 2, 0, 1850, 1650, 65, 45),
    _m("2014", "round_of_16", "Costa Rica", "Greece", 1, 1, 1600, 1650, 40, 45, 5, 3),
    # Quarter-finals
    _m("2014", "quarter_final", "Brazil", "Colombia", 2, 1, 2050, 1900, 85, 70),
    _m("2014", "quarter_final", "Netherlands", "Costa Rica", 0, 0, 1950, 1600, 75, 40, 4, 3),
    _m("2014", "quarter_final", "Germany", "France", 1, 0, 2100, 1850, 90, 65),
    _m("2014", "quarter_final", "Argentina", "Belgium", 1, 0, 2000, 1850, 80, 65),
    # Semi-finals
    _m("2014", "semi_final", "Brazil", "Germany", 1, 7, 2050, 2100, 85, 90),
    _m("2014", "semi_final", "Argentina", "Netherlands", 0, 0, 2000, 1950, 80, 75, 4, 2),
    # Third place & Final
    _m("2014", "third_place", "Brazil", "Netherlands", 0, 3, 2050, 1950, 85, 75),
    _m("2014", "final", "Germany", "Argentina", 1, 0, 2100, 2000, 90, 80),
]

# ============================================================
# 2018 World Cup (Russia) – 64 matches total
# ============================================================
MATCHES_2018: list[HistoricalMatchData] = [
    # Group A
    _m("2018", "group", "Russia", "Saudi Arabia", 5, 0, 1650, 1500, 45, 30),
    _m("2018", "group", "Egypt", "Uruguay", 0, 1, 1700, 1850, 50, 65),
    _m("2018", "group", "Russia", "Egypt", 3, 1, 1650, 1700, 45, 50),
    _m("2018", "group", "Uruguay", "Saudi Arabia", 1, 0, 1850, 1500, 65, 30),
    _m("2018", "group", "Uruguay", "Russia", 3, 0, 1850, 1650, 65, 45),
    _m("2018", "group", "Saudi Arabia", "Egypt", 2, 1, 1500, 1700, 30, 50),
    # Group B
    _m("2018", "group", "Portugal", "Spain", 3, 3, 1900, 2000, 70, 80),
    _m("2018", "group", "Morocco", "Iran", 0, 1, 1700, 1550, 50, 35),
    _m("2018", "group", "Portugal", "Morocco", 1, 0, 1900, 1700, 70, 50),
    _m("2018", "group", "Spain", "Iran", 1, 0, 2000, 1550, 80, 35),
    _m("2018", "group", "Spain", "Morocco", 2, 2, 2000, 1700, 80, 50),
    _m("2018", "group", "Iran", "Portugal", 1, 1, 1550, 1900, 35, 70),
    # Group C
    _m("2018", "group", "France", "Australia", 2, 1, 2050, 1650, 85, 45),
    _m("2018", "group", "Peru", "Denmark", 0, 1, 1700, 1700, 50, 50),
    _m("2018", "group", "France", "Peru", 1, 0, 2050, 1700, 85, 50),
    _m("2018", "group", "Denmark", "Australia", 1, 1, 1700, 1650, 50, 45),
    _m("2018", "group", "Denmark", "France", 0, 0, 1700, 2050, 50, 85),
    _m("2018", "group", "Australia", "Peru", 0, 2, 1650, 1700, 45, 50),
    # Group D
    _m("2018", "group", "Argentina", "Iceland", 1, 1, 1900, 1550, 70, 35),
    _m("2018", "group", "Croatia", "Nigeria", 2, 0, 1850, 1650, 65, 45),
    _m("2018", "group", "Argentina", "Croatia", 0, 3, 1900, 1850, 70, 65),
    _m("2018", "group", "Nigeria", "Iceland", 2, 0, 1650, 1550, 45, 35),
    _m("2018", "group", "Nigeria", "Argentina", 1, 2, 1650, 1900, 45, 70),
    _m("2018", "group", "Iceland", "Croatia", 1, 2, 1550, 1850, 35, 65),
    # Group E
    _m("2018", "group", "Brazil", "Switzerland", 1, 1, 2150, 1700, 92, 50),
    _m("2018", "group", "Costa Rica", "Serbia", 0, 1, 1550, 1750, 35, 55),
    _m("2018", "group", "Brazil", "Costa Rica", 2, 0, 2150, 1550, 92, 35),
    _m("2018", "group", "Serbia", "Switzerland", 1, 2, 1750, 1700, 55, 50),
    _m("2018", "group", "Serbia", "Brazil", 0, 2, 1750, 2150, 55, 92),
    _m("2018", "group", "Switzerland", "Costa Rica", 2, 2, 1700, 1550, 50, 35),
    # Group F
    _m("2018", "group", "Germany", "Mexico", 0, 1, 2000, 1750, 80, 55),
    _m("2018", "group", "Sweden", "South Korea", 1, 0, 1700, 1600, 50, 40),
    _m("2018", "group", "Germany", "Sweden", 2, 1, 2000, 1700, 80, 50),
    _m("2018", "group", "South Korea", "Mexico", 1, 2, 1600, 1750, 40, 55),
    _m("2018", "group", "South Korea", "Germany", 2, 0, 1600, 2000, 40, 80),
    _m("2018", "group", "Mexico", "Sweden", 0, 3, 1750, 1700, 55, 50),
    # Group G
    _m("2018", "group", "Belgium", "Panama", 3, 0, 1950, 1500, 75, 30),
    _m("2018", "group", "Tunisia", "England", 1, 2, 1650, 1900, 45, 70),
    _m("2018", "group", "Belgium", "Tunisia", 5, 2, 1950, 1650, 75, 45),
    _m("2018", "group", "England", "Panama", 6, 1, 1900, 1500, 70, 30),
    _m("2018", "group", "England", "Belgium", 0, 1, 1900, 1950, 70, 75),
    _m("2018", "group", "Panama", "Tunisia", 1, 2, 1500, 1650, 30, 45),
    # Group H
    _m("2018", "group", "Japan", "Colombia", 2, 1, 1550, 1850, 35, 65),
    _m("2018", "group", "Poland", "Senegal", 1, 2, 1750, 1700, 55, 50),
    _m("2018", "group", "Japan", "Senegal", 2, 2, 1550, 1700, 35, 50),
    _m("2018", "group", "Poland", "Colombia", 0, 3, 1750, 1850, 55, 65),
    _m("2018", "group", "Japan", "Poland", 0, 1, 1550, 1750, 35, 55),
    _m("2018", "group", "Senegal", "Colombia", 0, 1, 1700, 1850, 50, 65),
    # Round of 16
    _m("2018", "round_of_16", "France", "Argentina", 4, 3, 2050, 1900, 85, 70),
    _m("2018", "round_of_16", "Uruguay", "Portugal", 2, 1, 1850, 1900, 65, 70),
    _m("2018", "round_of_16", "Russia", "Spain", 1, 1, 1650, 1950, 45, 75, 4, 3),
    _m("2018", "round_of_16", "Croatia", "Denmark", 1, 1, 1850, 1700, 65, 50, 3, 2),
    _m("2018", "round_of_16", "Brazil", "Mexico", 2, 0, 2150, 1750, 92, 55),
    _m("2018", "round_of_16", "Belgium", "Japan", 3, 2, 1950, 1550, 75, 35),
    _m("2018", "round_of_16", "Sweden", "Switzerland", 1, 0, 1700, 1750, 50, 55),
    _m("2018", "round_of_16", "Colombia", "England", 1, 1, 1850, 1900, 65, 70, 3, 4),
    # Quarter-finals
    _m("2018", "quarter_final", "France", "Uruguay", 2, 0, 2050, 1850, 85, 65),
    _m("2018", "quarter_final", "Belgium", "Brazil", 2, 1, 1950, 2150, 75, 92),
    _m("2018", "quarter_final", "England", "Sweden", 2, 0, 1900, 1700, 70, 50),
    _m("2018", "quarter_final", "Russia", "Croatia", 2, 2, 1650, 1850, 45, 65, 3, 4),
    # Semi-finals
    _m("2018", "semi_final", "France", "Belgium", 1, 0, 2050, 1950, 85, 75),
    _m("2018", "semi_final", "Croatia", "England", 2, 1, 1850, 1900, 65, 70),
    # Third place & Final
    _m("2018", "third_place", "Belgium", "England", 2, 0, 1950, 1900, 75, 70),
    _m("2018", "final", "France", "Croatia", 4, 2, 2050, 1850, 85, 65),
]

# ============================================================
# 2022 World Cup (Qatar) – 64 matches total
# ============================================================
MATCHES_2022: list[HistoricalMatchData] = [
    # Group A
    _m("2022", "group", "Qatar", "Ecuador", 0, 2, 1500, 1700, 30, 50),
    _m("2022", "group", "Senegal", "Netherlands", 0, 2, 1700, 1950, 50, 75),
    _m("2022", "group", "Qatar", "Senegal", 1, 3, 1500, 1700, 30, 50),
    _m("2022", "group", "Netherlands", "Ecuador", 1, 1, 1950, 1700, 75, 50),
    _m("2022", "group", "Ecuador", "Senegal", 1, 2, 1700, 1700, 50, 50),
    _m("2022", "group", "Netherlands", "Qatar", 2, 0, 1950, 1500, 75, 30),
    # Group B
    _m("2022", "group", "England", "Iran", 6, 2, 1950, 1600, 75, 40),
    _m("2022", "group", "USA", "Wales", 1, 1, 1700, 1700, 50, 50),
    _m("2022", "group", "Wales", "Iran", 0, 2, 1700, 1600, 50, 40),
    _m("2022", "group", "England", "USA", 0, 0, 1950, 1700, 75, 50),
    _m("2022", "group", "Wales", "England", 0, 3, 1700, 1950, 50, 75),
    _m("2022", "group", "Iran", "USA", 0, 1, 1600, 1700, 40, 50),
    # Group C
    _m("2022", "group", "Argentina", "Saudi Arabia", 1, 2, 1950, 1500, 75, 30),
    _m("2022", "group", "Mexico", "Poland", 0, 0, 1750, 1750, 55, 55),
    _m("2022", "group", "Argentina", "Mexico", 2, 0, 1950, 1750, 75, 55),
    _m("2022", "group", "Poland", "Saudi Arabia", 2, 0, 1750, 1500, 55, 30),
    _m("2022", "group", "Poland", "Argentina", 0, 2, 1750, 1950, 55, 75),
    _m("2022", "group", "Saudi Arabia", "Mexico", 1, 2, 1500, 1750, 30, 55),
    # Group D
    _m("2022", "group", "Denmark", "Tunisia", 0, 0, 1750, 1650, 55, 45),
    _m("2022", "group", "France", "Australia", 4, 1, 2100, 1650, 90, 45),
    _m("2022", "group", "France", "Denmark", 2, 1, 2100, 1750, 90, 55),
    _m("2022", "group", "Tunisia", "Australia", 0, 1, 1650, 1650, 45, 45),
    _m("2022", "group", "Tunisia", "France", 1, 0, 1650, 2100, 45, 90),
    _m("2022", "group", "Australia", "Denmark", 1, 0, 1650, 1750, 45, 55),
    # Group E
    _m("2022", "group", "Germany", "Japan", 1, 2, 1950, 1600, 75, 40),
    _m("2022", "group", "Spain", "Costa Rica", 7, 0, 1950, 1550, 75, 35),
    _m("2022", "group", "Germany", "Spain", 1, 1, 1950, 1950, 75, 75),
    _m("2022", "group", "Japan", "Costa Rica", 0, 1, 1600, 1550, 40, 35),
    _m("2022", "group", "Japan", "Spain", 2, 1, 1600, 1950, 40, 75),
    _m("2022", "group", "Costa Rica", "Germany", 2, 4, 1550, 1950, 35, 75),
    # Group F
    _m("2022", "group", "Morocco", "Croatia", 0, 0, 1700, 1850, 50, 65),
    _m("2022", "group", "Belgium", "Canada", 1, 0, 1900, 1650, 70, 45),
    _m("2022", "group", "Belgium", "Morocco", 0, 2, 1900, 1700, 70, 50),
    _m("2022", "group", "Croatia", "Canada", 4, 1, 1850, 1650, 65, 45),
    _m("2022", "group", "Croatia", "Belgium", 0, 0, 1850, 1900, 65, 70),
    _m("2022", "group", "Canada", "Morocco", 1, 2, 1650, 1700, 45, 50),
    # Group G
    _m("2022", "group", "Brazil", "Serbia", 2, 0, 2200, 1750, 95, 55),
    _m("2022", "group", "Switzerland", "Cameroon", 1, 0, 1750, 1650, 55, 45),
    _m("2022", "group", "Brazil", "Switzerland", 1, 0, 2200, 1750, 95, 55),
    _m("2022", "group", "Cameroon", "Serbia", 3, 3, 1650, 1750, 45, 55),
    _m("2022", "group", "Cameroon", "Brazil", 1, 0, 1650, 2200, 45, 95),
    _m("2022", "group", "Serbia", "Switzerland", 2, 3, 1750, 1750, 55, 55),
    # Group H
    _m("2022", "group", "Uruguay", "South Korea", 0, 0, 1850, 1650, 65, 45),
    _m("2022", "group", "Portugal", "Ghana", 3, 2, 1900, 1700, 70, 50),
    _m("2022", "group", "Uruguay", "Portugal", 0, 2, 1850, 1900, 65, 70),
    _m("2022", "group", "South Korea", "Ghana", 2, 3, 1650, 1700, 45, 50),
    _m("2022", "group", "South Korea", "Portugal", 2, 1, 1650, 1900, 45, 70),
    _m("2022", "group", "Ghana", "Uruguay", 0, 2, 1700, 1850, 50, 65),
    # Round of 16
    _m("2022", "round_of_16", "Netherlands", "USA", 3, 1, 1950, 1700, 75, 50),
    _m("2022", "round_of_16", "Argentina", "Australia", 2, 1, 1950, 1650, 75, 45),
    _m("2022", "round_of_16", "France", "Poland", 3, 1, 2100, 1750, 90, 55),
    _m("2022", "round_of_16", "England", "Senegal", 3, 0, 1950, 1700, 75, 50),
    _m("2022", "round_of_16", "Japan", "Croatia", 1, 1, 1600, 1850, 40, 65, 1, 3),
    _m("2022", "round_of_16", "Brazil", "South Korea", 4, 1, 2200, 1650, 95, 45),
    _m("2022", "round_of_16", "Morocco", "Spain", 0, 0, 1700, 1950, 50, 75, 3, 0),
    _m("2022", "round_of_16", "Portugal", "Switzerland", 6, 1, 1900, 1750, 70, 55),
    # Quarter-finals
    _m("2022", "quarter_final", "Croatia", "Brazil", 1, 1, 1850, 2200, 65, 95, 4, 2),
    _m("2022", "quarter_final", "Netherlands", "Argentina", 2, 2, 1950, 1950, 75, 75, 3, 4),
    _m("2022", "quarter_final", "England", "France", 1, 2, 1950, 2100, 75, 90),
    _m("2022", "quarter_final", "Morocco", "Portugal", 1, 0, 1700, 1900, 50, 70),
    # Semi-finals
    _m("2022", "semi_final", "Argentina", "Croatia", 3, 0, 1950, 1850, 75, 65),
    _m("2022", "semi_final", "France", "Morocco", 2, 0, 2100, 1700, 90, 50),
    # Third place & Final
    _m("2022", "third_place", "Croatia", "Morocco", 2, 1, 1850, 1700, 65, 50),
    _m("2022", "final", "Argentina", "France", 3, 3, 1950, 2100, 75, 90, 4, 2),
]

ALL_HISTORICAL_MATCHES = MATCHES_2014 + MATCHES_2018 + MATCHES_2022
