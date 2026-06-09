"""
Historical World Cup matches for calibration (2014, 2018, 2022).
Includes approximate Elo ratings and IGF scores at the time of each tournament.
"""

from app.domain.calibration import HistoricalMatchData

# 2014 World Cup (Brazil)
MATCHES_2014 = [
    # Group stage
    HistoricalMatchData(tournament="2014", stage="group", home_team="Brazil", away_team="Croatia", home_goals=3, away_goals=1, home_elo=2050, away_elo=1750, home_igf=0.85, away_igf=0.55),
    HistoricalMatchData(tournament="2014", stage="group", home_team="Spain", away_team="Netherlands", home_goals=1, away_goals=5, home_elo=2000, away_elo=1950, home_igf=0.80, away_igf=0.75),
    HistoricalMatchData(tournament="2014", stage="group", home_team="Germany", away_team="Portugal", home_goals=4, away_goals=0, home_elo=2100, away_elo=1850, home_igf=0.90, away_igf=0.65),
    HistoricalMatchData(tournament="2014", stage="group", home_team="Argentina", away_team="Bosnia", home_goals=2, away_goals=1, home_elo=2000, away_elo=1700, home_igf=0.80, away_igf=0.50),
    HistoricalMatchData(tournament="2014", stage="group", home_team="Colombia", away_team="Greece", home_goals=3, away_goals=0, home_elo=1900, away_elo=1650, home_igf=0.70, away_igf=0.45),
    HistoricalMatchData(tournament="2014", stage="group", home_team="Costa Rica", away_team="Uruguay", home_goals=3, away_goals=1, home_elo=1600, away_elo=1800, home_igf=0.40, away_igf=0.60),
    # Round of 16
    HistoricalMatchData(tournament="2014", stage="round_of_16", home_team="Brazil", away_team="Chile", home_goals=1, away_goals=1, home_elo=2050, away_elo=1800, home_igf=0.85, away_igf=0.60, home_penalties=3, away_penalties=2),
    HistoricalMatchData(tournament="2014", stage="round_of_16", home_team="Netherlands", away_team="Mexico", home_goals=2, away_goals=1, home_elo=1950, away_elo=1750, home_igf=0.75, away_igf=0.55),
    HistoricalMatchData(tournament="2014", stage="round_of_16", home_team="Germany", away_team="Algeria", home_goals=2, away_goals=1, home_elo=2100, away_elo=1600, home_igf=0.90, away_igf=0.40),
    HistoricalMatchData(tournament="2014", stage="round_of_16", home_team="Argentina", away_team="Switzerland", home_goals=1, away_goals=0, home_elo=2000, away_elo=1750, home_igf=0.80, away_igf=0.55),
    HistoricalMatchData(tournament="2014", stage="round_of_16", home_team="Belgium", away_team="USA", home_goals=2, away_goals=1, home_elo=1850, away_elo=1700, home_igf=0.65, away_igf=0.50),
    HistoricalMatchData(tournament="2014", stage="round_of_16", home_team="Colombia", away_team="Uruguay", home_goals=2, away_goals=0, home_elo=1900, away_elo=1800, home_igf=0.70, away_igf=0.60),
    HistoricalMatchData(tournament="2014", stage="round_of_16", home_team="France", away_team="Nigeria", home_goals=2, away_goals=0, home_elo=1850, away_elo=1650, home_igf=0.65, away_igf=0.45),
    HistoricalMatchData(tournament="2014", stage="round_of_16", home_team="Costa Rica", away_team="Greece", home_goals=1, away_goals=1, home_elo=1600, away_elo=1650, home_igf=0.40, away_igf=0.45, home_penalties=5, away_penalties=3),
    # Quarter-finals
    HistoricalMatchData(tournament="2014", stage="quarter_final", home_team="Brazil", away_team="Colombia", home_goals=2, away_goals=1, home_elo=2050, away_elo=1900, home_igf=0.85, away_igf=0.70),
    HistoricalMatchData(tournament="2014", stage="quarter_final", home_team="Netherlands", away_team="Costa Rica", home_goals=0, away_goals=0, home_elo=1950, away_elo=1600, home_igf=0.75, away_igf=0.40, home_penalties=4, away_penalties=3),
    HistoricalMatchData(tournament="2014", stage="quarter_final", home_team="Germany", away_team="France", home_goals=1, away_goals=0, home_elo=2100, away_elo=1850, home_igf=0.90, away_igf=0.65),
    HistoricalMatchData(tournament="2014", stage="quarter_final", home_team="Argentina", away_team="Belgium", home_goals=1, away_goals=0, home_elo=2000, away_elo=1850, home_igf=0.80, away_igf=0.65),
    # Semi-finals
    HistoricalMatchData(tournament="2014", stage="semi_final", home_team="Brazil", away_team="Germany", home_goals=1, away_goals=7, home_elo=2050, away_elo=2100, home_igf=0.85, away_igf=0.90),
    HistoricalMatchData(tournament="2014", stage="semi_final", home_team="Argentina", away_team="Netherlands", home_goals=0, away_goals=0, home_elo=2000, away_elo=1950, home_igf=0.80, away_igf=0.75, home_penalties=4, away_penalties=2),
    # Third place
    HistoricalMatchData(tournament="2014", stage="third_place", home_team="Brazil", away_team="Netherlands", home_goals=0, away_goals=3, home_elo=2050, away_elo=1950, home_igf=0.85, away_igf=0.75),
    # Final
    HistoricalMatchData(tournament="2014", stage="final", home_team="Germany", away_team="Argentina", home_goals=1, away_goals=0, home_elo=2100, away_elo=2000, home_igf=0.90, away_igf=0.80),
]

# 2018 World Cup (Russia)
MATCHES_2018 = [
    # Group stage
    HistoricalMatchData(tournament="2018", stage="group", home_team="Russia", away_team="Saudi Arabia", home_goals=5, away_goals=0, home_elo=1650, away_elo=1500, home_igf=0.45, away_igf=0.30),
    HistoricalMatchData(tournament="2018", stage="group", home_team="Germany", away_team="Mexico", home_goals=0, away_goals=1, home_elo=2000, away_elo=1750, home_igf=0.80, away_igf=0.55),
    HistoricalMatchData(tournament="2018", stage="group", home_team="Brazil", away_team="Switzerland", home_goals=1, away_goals=1, home_elo=2150, away_elo=1700, home_igf=0.92, away_igf=0.50),
    HistoricalMatchData(tournament="2018", stage="group", home_team="Argentina", away_team="Iceland", home_goals=1, away_goals=1, home_elo=1900, away_elo=1550, home_igf=0.70, away_igf=0.35),
    HistoricalMatchData(tournament="2018", stage="group", home_team="France", away_team="Peru", home_goals=1, away_goals=0, home_elo=2050, away_elo=1700, home_igf=0.85, away_igf=0.50),
    HistoricalMatchData(tournament="2018", stage="group", home_team="Japan", away_team="Colombia", home_goals=2, away_goals=1, home_elo=1550, away_elo=1850, home_igf=0.35, away_igf=0.65),
    # Round of 16
    HistoricalMatchData(tournament="2018", stage="round_of_16", home_team="France", away_team="Argentina", home_goals=4, away_goals=3, home_elo=2050, away_elo=1900, home_igf=0.85, away_igf=0.70),
    HistoricalMatchData(tournament="2018", stage="round_of_16", home_team="Uruguay", away_team="Portugal", home_goals=2, away_goals=1, home_elo=1850, away_elo=1900, home_igf=0.65, away_igf=0.70),
    HistoricalMatchData(tournament="2018", stage="round_of_16", home_team="Russia", away_team="Spain", home_goals=1, away_goals=1, home_elo=1650, away_elo=1950, home_igf=0.45, away_igf=0.75, home_penalties=4, away_penalties=3),
    HistoricalMatchData(tournament="2018", stage="round_of_16", home_team="Croatia", away_team="Denmark", home_goals=1, away_goals=1, home_elo=1850, away_elo=1700, home_igf=0.65, away_igf=0.50, home_penalties=3, away_penalties=2),
    HistoricalMatchData(tournament="2018", stage="round_of_16", home_team="Brazil", away_team="Mexico", home_goals=2, away_goals=0, home_elo=2150, away_elo=1750, home_igf=0.92, away_igf=0.55),
    HistoricalMatchData(tournament="2018", stage="round_of_16", home_team="Belgium", away_team="Japan", home_goals=3, away_goals=2, home_elo=1950, away_elo=1550, home_igf=0.75, away_igf=0.35),
    HistoricalMatchData(tournament="2018", stage="round_of_16", home_team="Sweden", away_team="Switzerland", home_goals=1, away_goals=0, home_elo=1700, away_elo=1750, home_igf=0.50, away_igf=0.55),
    HistoricalMatchData(tournament="2018", stage="round_of_16", home_team="Colombia", away_team="England", home_goals=1, away_goals=1, home_elo=1850, away_elo=1900, home_igf=0.65, away_igf=0.70, away_penalties=4, home_penalties=3),
    # Quarter-finals
    HistoricalMatchData(tournament="2018", stage="quarter_final", home_team="France", away_team="Uruguay", home_goals=2, away_goals=0, home_elo=2050, away_elo=1850, home_igf=0.85, away_igf=0.65),
    HistoricalMatchData(tournament="2018", stage="quarter_final", home_team="Belgium", away_team="Brazil", home_goals=2, away_goals=1, home_elo=1950, away_elo=2150, home_igf=0.75, away_igf=0.92),
    HistoricalMatchData(tournament="2018", stage="quarter_final", home_team="England", away_team="Sweden", home_goals=2, away_goals=0, home_elo=1900, away_elo=1700, home_igf=0.70, away_igf=0.50),
    HistoricalMatchData(tournament="2018", stage="quarter_final", home_team="Russia", away_team="Croatia", home_goals=2, away_goals=2, home_elo=1650, away_elo=1850, home_igf=0.45, away_igf=0.65, away_penalties=4, home_penalties=3),
    # Semi-finals
    HistoricalMatchData(tournament="2018", stage="semi_final", home_team="France", away_team="Belgium", home_goals=1, away_goals=0, home_elo=2050, away_elo=1950, home_igf=0.85, away_igf=0.75),
    HistoricalMatchData(tournament="2018", stage="semi_final", home_team="Croatia", away_team="England", home_goals=2, away_goals=1, home_elo=1850, away_elo=1900, home_igf=0.65, away_igf=0.70),
    # Third place
    HistoricalMatchData(tournament="2018", stage="third_place", home_team="Belgium", away_team="England", home_goals=2, away_goals=0, home_elo=1950, away_elo=1900, home_igf=0.75, away_igf=0.70),
    # Final
    HistoricalMatchData(tournament="2018", stage="final", home_team="France", away_team="Croatia", home_goals=4, away_goals=2, home_elo=2050, away_elo=1850, home_igf=0.85, away_igf=0.65),
]

# 2022 World Cup (Qatar)
MATCHES_2022 = [
    # Group stage
    HistoricalMatchData(tournament="2022", stage="group", home_team="Argentina", away_team="Saudi Arabia", home_goals=1, away_goals=2, home_elo=1950, away_elo=1500, home_igf=0.75, away_igf=0.30),
    HistoricalMatchData(tournament="2022", stage="group", home_team="Germany", away_team="Japan", home_goals=1, away_goals=2, home_elo=1950, away_elo=1600, home_igf=0.75, away_igf=0.40),
    HistoricalMatchData(tournament="2022", stage="group", home_team="Spain", away_team="Costa Rica", home_goals=7, away_goals=0, home_elo=1950, away_elo=1550, home_igf=0.75, away_igf=0.35),
    HistoricalMatchData(tournament="2022", stage="group", home_team="Brazil", away_team="Serbia", home_goals=2, away_goals=0, home_elo=2200, away_elo=1700, home_igf=0.95, away_igf=0.50),
    HistoricalMatchData(tournament="2022", stage="group", home_team="France", away_team="Australia", home_goals=4, away_goals=1, home_elo=2100, away_elo=1550, home_igf=0.90, away_igf=0.35),
    HistoricalMatchData(tournament="2022", stage="group", home_team="Japan", away_team="Spain", home_goals=2, away_goals=1, home_elo=1600, away_elo=1950, home_igf=0.40, away_igf=0.75),
    # Round of 16
    HistoricalMatchData(tournament="2022", stage="round_of_16", home_team="Netherlands", away_team="USA", home_goals=3, away_goals=1, home_elo=1950, away_elo=1700, home_igf=0.75, away_igf=0.50),
    HistoricalMatchData(tournament="2022", stage="round_of_16", home_team="Argentina", away_team="Australia", home_goals=2, away_goals=1, home_elo=1950, away_elo=1550, home_igf=0.75, away_igf=0.35),
    HistoricalMatchData(tournament="2022", stage="round_of_16", home_team="France", away_team="Poland", home_goals=3, away_goals=1, home_elo=2100, away_elo=1700, home_igf=0.90, away_igf=0.50),
    HistoricalMatchData(tournament="2022", stage="round_of_16", home_team="England", away_team="Senegal", home_goals=3, away_goals=0, home_elo=1950, away_elo=1650, home_igf=0.75, away_igf=0.45),
    HistoricalMatchData(tournament="2022", stage="round_of_16", home_team="Japan", away_team="Croatia", home_goals=1, away_goals=1, home_elo=1600, away_elo=1850, home_igf=0.40, away_igf=0.65, away_penalties=3, home_penalties=1),
    HistoricalMatchData(tournament="2022", stage="round_of_16", home_team="Brazil", away_team="South Korea", home_goals=4, away_goals=1, home_elo=2200, away_elo=1650, home_igf=0.95, away_igf=0.45),
    HistoricalMatchData(tournament="2022", stage="round_of_16", home_team="Morocco", away_team="Spain", home_goals=0, away_goals=0, home_elo=1700, away_elo=1950, home_igf=0.50, away_igf=0.75, home_penalties=3, away_penalties=0),
    HistoricalMatchData(tournament="2022", stage="round_of_16", home_team="Portugal", away_team="Switzerland", home_goals=6, away_goals=1, home_elo=1900, away_elo=1750, home_igf=0.70, away_igf=0.55),
    # Quarter-finals
    HistoricalMatchData(tournament="2022", stage="quarter_final", home_team="Croatia", away_team="Brazil", home_goals=1, away_goals=1, home_elo=1850, away_elo=2200, home_igf=0.65, away_igf=0.95, home_penalties=4, away_penalties=2),
    HistoricalMatchData(tournament="2022", stage="quarter_final", home_team="Netherlands", away_team="Argentina", home_goals=2, away_goals=2, home_elo=1950, away_elo=1950, home_igf=0.75, away_igf=0.75, away_penalties=4, home_penalties=3),
    HistoricalMatchData(tournament="2022", stage="quarter_final", home_team="England", away_team="France", home_goals=1, away_goals=2, home_elo=1950, away_elo=2100, home_igf=0.75, away_igf=0.90),
    HistoricalMatchData(tournament="2022", stage="quarter_final", home_team="Morocco", away_team="Portugal", home_goals=1, away_goals=0, home_elo=1700, away_elo=1900, home_igf=0.50, away_igf=0.70),
    # Semi-finals
    HistoricalMatchData(tournament="2022", stage="semi_final", home_team="Argentina", away_team="Croatia", home_goals=3, away_goals=0, home_elo=1950, away_elo=1850, home_igf=0.75, away_igf=0.65),
    HistoricalMatchData(tournament="2022", stage="semi_final", home_team="France", away_team="Morocco", home_goals=2, away_goals=0, home_elo=2100, away_elo=1700, home_igf=0.90, away_igf=0.50),
    # Third place
    HistoricalMatchData(tournament="2022", stage="third_place", home_team="Croatia", away_team="Morocco", home_goals=2, away_goals=1, home_elo=1850, away_elo=1700, home_igf=0.65, away_igf=0.50),
    # Final
    HistoricalMatchData(tournament="2022", stage="final", home_team="Argentina", away_team="France", home_goals=3, away_goals=3, home_elo=1950, away_elo=2100, home_igf=0.75, away_igf=0.90, home_penalties=4, away_penalties=2),
]

ALL_HISTORICAL_MATCHES = MATCHES_2014 + MATCHES_2018 + MATCHES_2022
