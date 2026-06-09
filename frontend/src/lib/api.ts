const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface Team {
  id: string;
  name: string;
  fifa_code: string | null;
  flag_url: string | null;
  continent: string | null;
  founded_year: number | null;
  is_national_team: boolean;
}

export interface Match {
  id: string;
  competition_id: string;
  home_team_id: string;
  away_team_id: string;
  match_date: string;
  stage: string;
  group_name: string | null;
  home_goals: number | null;
  away_goals: number | null;
  home_xg: number | null;
  away_xg: number | null;
  is_neutral_venue: boolean;
  status: string;
}

export interface MatchPrediction {
  match_id: string;
  home_team: string;
  away_team: string;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  home_expected_goals: number;
  away_expected_goals: number;
  most_likely_score: string;
}

export interface GroupStanding {
  id: string;
  group_id: string;
  team_id: string;
  team_name: string;
  position: number;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  qualified: boolean;
}

export interface GroupDetail {
  id: string;
  competition_id: string;
  name: string;
  stage: string;
  standings: GroupStanding[];
}

export interface IGFScore {
  team_id: string;
  team_name: string;
  igf_score: number;
  components: Record<string, number>;
}

export interface Simulation {
  id: string;
  competition_id: string;
  name: string | null;
  num_simulations: number;
  status: string;
  created_at: string;
  completed_at: string | null;
}

export interface SimulationResult {
  id: string;
  team_id: string;
  team_name: string;
  group_name: string | null;
  group_position: number | null;
  reached_round_of_16: number;
  reached_quarter_final: number;
  reached_semi_final: number;
  reached_final: number;
  won_tournament: number;
  points: number;
}

export interface SimulationDetail extends Simulation {
  results: SimulationResult[];
}

export const api = {
  teams: {
    list: (page = 1, perPage = 20) =>
      fetchJSON<Team[]>(`/teams?page=${page}&per_page=${perPage}`),
    get: (id: string) => fetchJSON<Team>(`/teams/${id}`),
  },
  matches: {
    list: (page = 1, perPage = 20, stage?: string) => {
      let path = `/matches?page=${page}&per_page=${perPage}`;
      if (stage) path += `&stage=${stage}`;
      return fetchJSON<Match[]>(path);
    },
    get: (id: string) => fetchJSON<Match>(`/matches/${id}`),
    predict: (id: string) =>
      fetchJSON<MatchPrediction>(`/matches/${id}/prediction`),
  },
  groups: {
    list: () => fetchJSON<GroupDetail[]>("/groups"),
    get: (id: string) => fetchJSON<GroupDetail>(`/groups/${id}`),
  },
  rankings: {
    elo: () => fetchJSON<any[]>("/rankings/elo"),
    fifa: () => fetchJSON<any[]>("/rankings/fifa"),
    igf: () => fetchJSON<IGFScore[]>("/rankings/igf"),
  },
  predictions: {
    list: () => fetchJSON<MatchPrediction[]>("/predictions"),
    rankings: () => fetchJSON<IGFScore[]>("/predictions/rankings"),
  },
  simulations: {
    list: () => fetchJSON<Simulation[]>("/simulations"),
    get: (id: string) => fetchJSON<SimulationDetail>(`/simulations/${id}`),
    create: (data: { competition_id: string; num_simulations: number }) =>
      fetchJSON<Simulation>("/simulations", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    run: (id: string) =>
      fetchJSON<SimulationDetail>(`/simulations/${id}/run`, { method: "POST" }),
  },
};
