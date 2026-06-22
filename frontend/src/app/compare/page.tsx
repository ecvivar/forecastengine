"use client";

import { useEffect, useState, useMemo } from "react";
import { api, Team, IGFScore } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import TeamRadarChart from "@/components/TeamRadarChart";
import ProbabilityBar from "@/components/ProbabilityBar";
import { getContinentColor, getConfidenceColor, getConfidenceLabel } from "@/lib/utils";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Legend,
} from "recharts";
import { ArrowRightLeft, Shield, BarChart3, Swords, BrainCircuit, Scale, Trophy, Target, ArrowRight, Users } from "lucide-react";

const TABS = [
  { id: "profiles", label: "Team Profiles", icon: Users },
  { id: "h2h", label: "H2H Prediction", icon: Swords },
  { id: "explainability", label: "Explainability", icon: BrainCircuit },
] as const;

type TabId = (typeof TABS)[number]["id"];

interface ComparisonData {
  team_a: any;
  team_b: any;
  head_to_head_prediction: any;
}

interface ExplainData {
  prediction: any;
  drivers: Record<string, any>;
  [key: string]: any;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function ComparePage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [igfScores, setIgfScores] = useState<IGFScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [teamA, setTeamA] = useState<string>("");
  const [teamB, setTeamB] = useState<string>("");
  const [activeTab, setActiveTab] = useState<TabId>("profiles");
  const [comparison, setComparison] = useState<ComparisonData | null>(null);
  const [explain, setExplain] = useState<ExplainData | null>(null);
  const [comparing, setComparing] = useState(false);
  const [teamAId, setTeamAId] = useState<string>("");
  const [teamBId, setTeamBId] = useState<string>("");

  const teamById = useMemo(() => new Map(teams.map((t) => [t.id, t])), [teams]);
  const teamByName = useMemo(() => new Map(teams.map((t) => [t.name, t])), [teams]);

  useEffect(() => {
    Promise.all([
      api.teams.list(1, 100),
      api.rankings.igf().catch(() => [] as IGFScore[]),
    ])
      .then(([t, igf]) => {
        setTeams(t);
        setIgfScores(igf);
        if (t.length >= 2) {
          setTeamA(t[0].name);
          setTeamB(t[1].name);
          setTeamAId(t[0].id);
          setTeamBId(t[1].id);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const igfMap = useMemo(() => new Map(igfScores.map((s) => [s.team_name, s])), [igfScores]);
  const teamNames = useMemo(() => teams.map((t) => t.name).sort(), [teams]);

  const handleTeamAChange = (name: string) => {
    setTeamA(name);
    setTeamAId(teamByName.get(name)?.id || "");
    setComparison(null);
    setExplain(null);
  };

  const handleTeamBChange = (name: string) => {
    setTeamB(name);
    setTeamBId(teamByName.get(name)?.id || "");
    setComparison(null);
    setExplain(null);
  };

  const fetchComparison = async () => {
    if (!teamAId || !teamBId || teamAId === teamBId) return;
    setComparing(true);
    try {
      const [comp, expl] = await Promise.all([
        api.comparison.compare(teamAId, teamBId),
        fetch(`${API_URL}/matches/explain?home_team_id=${teamAId}&away_team_id=${teamBId}&home_advantage=true`).then((r) => r.ok ? r.json() : null),
      ]);
      setComparison(comp);
      setExplain(expl);
    } catch (e) {
      console.error(e);
    } finally {
      setComparing(false);
    }
  };

  const componentsA = useMemo(() => {
    if (!teamA) return {};
    return igfMap.get(teamA)?.components || {};
  }, [teamA, igfMap]);

  const componentsB = useMemo(() => {
    if (!teamB) return {};
    return igfMap.get(teamB)?.components || {};
  }, [teamB, igfMap]);

  const radarComparison = useMemo(() => {
    const keys = new Set([...Object.keys(componentsA), ...Object.keys(componentsB)]);
    return Array.from(keys).map((key) => ({
      component: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      [teamA || "Team A"]: (componentsA[key] || 0) * 100,
      [teamB || "Team B"]: (componentsB[key] || 0) * 100,
    }));
  }, [componentsA, componentsB, teamA, teamB]);

  if (loading) return <SkeletonPage />;

  const StatRow = ({ label, a, b, fmt = (v: any) => v, unit = "" }: { label: string; a: any; b: any; fmt?: (v: any) => any; unit?: string }) => (
    <div className="flex items-center justify-between py-2 border-b border-[hsl(var(--border))] last:border-0">
      <span className="text-sm text-[hsl(var(--muted))] w-1/3">{label}</span>
      <span className="text-sm font-semibold text-right w-1/3">{fmt(a)}{unit}</span>
      <span className="text-xs text-[hsl(var(--muted))] w-8 text-center">
        {a != null && b != null ? (
          a > b ? "▲" : a < b ? "▼" : "—"
        ) : "—"}
      </span>
      <span className="text-sm font-semibold text-right w-1/3">{fmt(b)}{unit}</span>
    </div>
  );

  const c = comparison;
  const igfA = teamA ? igfMap.get(teamA) : null;
  const igfB = teamB ? igfMap.get(teamB) : null;

  return (
    <div className="container-page space-y-6">
      <div>
        <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">Analysis</div>
        <h1 className="page-title">Team Comparison</h1>
        <p className="page-subtitle">Compare IGF profiles, head-to-head predictions, and explainability drivers side by side.</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex items-end gap-4 flex-wrap">
            <div className="flex-1 min-w-[160px]">
              <label className="text-xs text-[hsl(var(--muted))] mb-1 block">Team A</label>
              <select
                value={teamA}
                onChange={(e) => handleTeamAChange(e.target.value)}
                className="w-full px-3 py-2 border border-[hsl(var(--border))] rounded-lg text-sm bg-transparent"
              >
                <option value="">Select team...</option>
                {teamNames.filter((n) => n !== teamB).map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>
            <div className="pb-2">
              <ArrowRightLeft className="w-5 h-5 text-[hsl(var(--muted))]" />
            </div>
            <div className="flex-1 min-w-[160px]">
              <label className="text-xs text-[hsl(var(--muted))] mb-1 block">Team B</label>
              <select
                value={teamB}
                onChange={(e) => handleTeamBChange(e.target.value)}
                className="w-full px-3 py-2 border border-[hsl(var(--border))] rounded-lg text-sm bg-transparent"
              >
                <option value="">Select team...</option>
                {teamNames.filter((n) => n !== teamA).map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </div>
            <button
              onClick={fetchComparison}
              disabled={comparing || teamA === teamB || !teamA || !teamB}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              {comparing ? "Loading..." : "Compare"}
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-[hsl(var(--border))]">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-primary-600 text-primary-700"
                : "border-transparent text-[hsl(var(--muted))] hover:text-[hsl(var(--foreground))]"
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB: Team Profiles */}
      {activeTab === "profiles" && teamA && teamB && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <BarChart3 className="w-4 h-4 text-blue-500" />
                  IGF Profile — {teamA}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <TeamRadarChart teamName={teamA} components={componentsA} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <BarChart3 className="w-4 h-4 text-green-500" />
                  IGF Profile — {teamB}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <TeamRadarChart teamName={teamB} components={componentsB} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Shield className="w-4 h-4 text-purple-500" />
                Direct Comparison
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarComparison}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="component" tick={{ fontSize: 10 }} />
                    <Radar dataKey={teamA} fill="#3b82f6" fillOpacity={0.2} stroke="#3b82f6" strokeWidth={2} />
                    <Radar dataKey={teamB} fill="#22c55e" fillOpacity={0.2} stroke="#22c55e" strokeWidth={2} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-2 gap-4">
            {[
              { label: "IGF Score", a: igfA?.igf_score?.toFixed(1) || "—", b: igfB?.igf_score?.toFixed(1) || "—" },
              { label: "Continent", a: teamByName.get(teamA)?.continent || "—", b: teamByName.get(teamB)?.continent || "—" },
            ].map((s) => (
              <Card key={s.label}>
                <CardContent className="p-3 flex items-center justify-between text-sm">
                  <span className="text-[hsl(var(--muted))]">{s.label}</span>
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-blue-600">{s.a}</span>
                    <span className="text-[hsl(var(--muted))] text-xs">vs</span>
                    <span className="font-medium text-green-600">{s.b}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* TAB: H2H Prediction */}
      {activeTab === "h2h" && (
        <>
          {!comparison && !comparing && (
            <Card>
              <CardContent className="p-8 text-center text-[hsl(var(--muted))]">
                <Swords className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Select two teams and click Compare to load the head-to-head prediction.</p>
              </CardContent>
            </Card>
          )}

          {comparing && <SkeletonPage />}

          {comparison && (
            <div className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <Card className="border-2 border-blue-200">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-blue-700">
                      <Trophy className="w-5 h-5" /> {comparison.team_a.team_name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-1 mb-4">
                      <Badge className={getContinentColor(comparison.team_a.continent)}>
                        {comparison.team_a.continent || "Unknown"}
                      </Badge>
                      {comparison.team_a.fifa_code && (
                        <span className="text-xs text-[hsl(var(--muted))] ml-2">FIFA: {comparison.team_a.fifa_code}</span>
                      )}
                    </div>
                    <TeamRadarChart
                      teamName={comparison.team_a.team_name}
                      components={igfMap.get(comparison.team_a.team_name)?.components || {}}
                    />
                  </CardContent>
                </Card>

                <Card className="border-2 border-red-200">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-red-700">
                      <Target className="w-5 h-5" /> {comparison.team_b.team_name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-1 mb-4">
                      <Badge className={getContinentColor(comparison.team_b.continent)}>
                        {comparison.team_b.continent || "Unknown"}
                      </Badge>
                      {comparison.team_b.fifa_code && (
                        <span className="text-xs text-[hsl(var(--muted))] ml-2">FIFA: {comparison.team_b.fifa_code}</span>
                      )}
                    </div>
                    <TeamRadarChart
                      teamName={comparison.team_b.team_name}
                      components={igfMap.get(comparison.team_b.team_name)?.components || {}}
                    />
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Head-to-Head Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between mb-4 text-sm font-semibold pb-2 border-b border-[hsl(var(--border))]">
                    <span className="w-1/3 text-blue-600">{comparison.team_a.team_name}</span>
                    <span className="w-8 text-center text-[hsl(var(--muted))] text-xs">VS</span>
                    <span className="w-1/3 text-red-600 text-right">{comparison.team_b.team_name}</span>
                  </div>
                  <StatRow label="Elo Score" a={comparison.team_a.elo_score} b={comparison.team_b.elo_score} fmt={Math.round} />
                  <StatRow label="IGF Score" a={comparison.team_a.igf_score} b={comparison.team_b.igf_score} fmt={(v: number) => v.toFixed(1)} />
                  <StatRow label="FIFA Rank" a={comparison.team_a.fifa_rank} b={comparison.team_b.fifa_rank} fmt={(v: any) => v ?? "—"} />
                  <StatRow label="Group" a={comparison.team_a.group_name} b={comparison.team_b.group_name} fmt={(v: any) => v ?? "—"} />
                  <StatRow label="Group Position" a={comparison.team_a.group_position} b={comparison.team_b.group_position} fmt={(v: any) => v ?? "—"} />
                  <StatRow label="Group Points" a={comparison.team_a.group_points} b={comparison.team_b.group_points} fmt={(v: any) => v ?? "—"} />
                  {comparison.team_a.xg_for != null && (
                    <StatRow label="xG For" a={comparison.team_a.xg_for} b={comparison.team_b.xg_for} fmt={(v: number) => v.toFixed(2)} />
                  )}
                  {comparison.team_a.xg_against != null && (
                    <StatRow label="xG Against" a={comparison.team_a.xg_against} b={comparison.team_b.xg_against} fmt={(v: number) => v.toFixed(2)} />
                  )}
                </CardContent>
              </Card>

              <div className="grid gap-6 md:grid-cols-2">
                {comparison.team_a.simulation && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">{comparison.team_a.team_name} — Tournament Outlook</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <div className="flex justify-between"><span className="text-[hsl(var(--muted))]">Win Tournament</span><span className="font-semibold text-green-600">{comparison.team_a.simulation.win_prob}%</span></div>
                      <div className="flex justify-between"><span className="text-[hsl(var(--muted))]">Reach Final</span><span className="font-semibold">{comparison.team_a.simulation.final_prob}%</span></div>
                      <div className="flex justify-between"><span className="text-[hsl(var(--muted))]">Reach Semi-Final</span><span className="font-semibold">{comparison.team_a.simulation.sf_prob}%</span></div>
                      <div className="flex justify-between"><span className="text-[hsl(var(--muted))]">Reach QF</span><span className="font-semibold">{comparison.team_a.simulation.qf_prob}%</span></div>
                      <div className="flex justify-between"><span className="text-[hsl(var(--muted))]">Avg Points</span><span className="font-semibold">{comparison.team_a.simulation.avg_points}</span></div>
                    </CardContent>
                  </Card>
                )}
                {comparison.team_b.simulation && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">{comparison.team_b.team_name} — Tournament Outlook</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <div className="flex justify-between"><span className="text-[hsl(var(--muted))]">Win Tournament</span><span className="font-semibold text-green-600">{comparison.team_b.simulation.win_prob}%</span></div>
                      <div className="flex justify-between"><span className="text-[hsl(var(--muted))]">Reach Final</span><span className="font-semibold">{comparison.team_b.simulation.final_prob}%</span></div>
                      <div className="flex justify-between"><span className="text-[hsl(var(--muted))]">Reach Semi-Final</span><span className="font-semibold">{comparison.team_b.simulation.sf_prob}%</span></div>
                      <div className="flex justify-between"><span className="text-[hsl(var(--muted))]">Reach QF</span><span className="font-semibold">{comparison.team_b.simulation.qf_prob}%</span></div>
                      <div className="flex justify-between"><span className="text-[hsl(var(--muted))]">Avg Points</span><span className="font-semibold">{comparison.team_b.simulation.avg_points}</span></div>
                    </CardContent>
                  </Card>
                )}
              </div>

              {comparison.head_to_head_prediction && (
                <Card className="border-2 border-primary-200">
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <ArrowRight className="w-5 h-5 text-primary-600" />
                      Head-to-Head Prediction
                      {comparison.head_to_head_prediction.confidence_index != null && (
                        <Badge className={getConfidenceColor(comparison.head_to_head_prediction.confidence_index)}>
                          {getConfidenceLabel(comparison.head_to_head_prediction.confidence_index)}
                        </Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <ProbabilityBar
                      homeWin={comparison.head_to_head_prediction.home_win_prob}
                      draw={comparison.head_to_head_prediction.draw_prob}
                      awayWin={comparison.head_to_head_prediction.away_win_prob}
                      homeLabel={comparison.team_a.team_name}
                      awayLabel={comparison.team_b.team_name}
                    />
                    <div className="grid grid-cols-3 gap-4 text-center text-sm">
                      <div>
                        <div className="text-blue-600 font-bold text-lg">{comparison.head_to_head_prediction.home_win_prob.toFixed(1)}%</div>
                        <div className="text-[hsl(var(--muted))] text-xs">Home Win</div>
                      </div>
                      <div>
                        <div className="font-bold text-lg">{comparison.head_to_head_prediction.draw_prob.toFixed(1)}%</div>
                        <div className="text-[hsl(var(--muted))] text-xs">Draw</div>
                      </div>
                      <div>
                        <div className="text-red-600 font-bold text-lg">{comparison.head_to_head_prediction.away_win_prob.toFixed(1)}%</div>
                        <div className="text-[hsl(var(--muted))] text-xs">Away Win</div>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                      <div className="panel p-3 text-center">
                        <div className="text-[hsl(var(--muted))] text-xs">Most Likely Score</div>
                        <div className="font-semibold">{comparison.head_to_head_prediction.most_likely_score}</div>
                      </div>
                      <div className="panel p-3 text-center">
                        <div className="text-[hsl(var(--muted))] text-xs">BTTS</div>
                        <div className="font-semibold">{(comparison.head_to_head_prediction.btts_prob * 100).toFixed(0)}%</div>
                      </div>
                      <div className="panel p-3 text-center">
                        <div className="text-[hsl(var(--muted))] text-xs">Over 2.5</div>
                        <div className="font-semibold">{(comparison.head_to_head_prediction.over_25_prob * 100).toFixed(0)}%</div>
                      </div>
                      <div className="panel p-3 text-center">
                        <div className="text-[hsl(var(--muted))] text-xs">Surprise Risk</div>
                        <div className="font-semibold">{(comparison.head_to_head_prediction.surprise_risk * 100).toFixed(0)}%</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </>
      )}

      {/* TAB: Explainability */}
      {activeTab === "explainability" && (
        <>
          {!explain && !comparing && (
            <Card>
              <CardContent className="p-8 text-center text-[hsl(var(--muted))]">
                <BrainCircuit className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Select two teams and click Compare to reveal prediction drivers.</p>
              </CardContent>
            </Card>
          )}

          {explain && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <BrainCircuit className="w-4 h-4 text-purple-500" />
                  Prediction Drivers
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {explain.drivers && Object.entries(explain.drivers).map(([key, val]: [string, any]) => (
                  <div key={key} className="flex items-center justify-between py-2 border-b border-[hsl(var(--border))] last:border-0">
                    <span className="text-sm font-medium capitalize">{key.replace(/_/g, " ")}</span>
                    <span className="text-sm font-mono font-semibold">
                      {typeof val === "number" ? (val > 1 ? val.toFixed(2) : (val * 100).toFixed(1) + "%") : String(val)}
                    </span>
                  </div>
                ))}
                {!explain.drivers && (
                  <div className="text-sm text-[hsl(var(--muted))] italic">Raw explanation object:</div>
                )}
              </CardContent>
            </Card>
          )}

          {explain?.prediction && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Scale className="w-4 h-4 text-green-500" />
                  Prediction Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent>
                {explain.prediction.most_likely_score && (
                  <div className="text-center mb-4">
                    <span className="text-2xl font-bold">{explain.prediction.most_likely_score}</span>
                    <span className="text-sm text-[hsl(var(--muted))] ml-2">most likely score</span>
                  </div>
                )}
                <div className="grid grid-cols-3 gap-4 text-center">
                  {[
                    { label: "Home Win", key: "home_win_prob", color: "text-blue-600" },
                    { label: "Draw", key: "draw_prob", color: "" },
                    { label: "Away Win", key: "away_win_prob", color: "text-red-600" },
                  ].map((item) => (
                    <div key={item.key}>
                      <div className={`font-bold text-lg ${item.color}`}>
                        {((explain.prediction[item.key] || 0) * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-[hsl(var(--muted))]">{item.label}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {(!teamA || !teamB) && activeTab === "profiles" && (
        <Card>
          <CardContent className="p-8 text-center text-[hsl(var(--muted))]">
            <ArrowRightLeft className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Select two teams above to compare their IGF profiles.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
