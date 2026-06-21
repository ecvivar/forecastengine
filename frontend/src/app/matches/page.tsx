"use client";

import { useEffect, useState, useMemo } from "react";
import { api, Match, FullMatchPrediction } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import ProbabilityBar from "@/components/ProbabilityBar";
import { formatDate, getStageLabel, getConfidenceColor, getConfidenceLabel } from "@/lib/utils";
import { ChevronDown, ChevronRight, Activity, AlertTriangle, Target, BarChart3 } from "lucide-react";

export default function MatchesPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [predictions, setPredictions] = useState<Map<string, FullMatchPrediction>>(new Map());
  const [loading, setLoading] = useState(true);
  const [expandedMatches, setExpandedMatches] = useState<Set<string>>(new Set());
  const [expandedStage, setExpandedStage] = useState<string | null>(null);

  useEffect(() => {
    api.matches.list(1, 104).then(async (ms) => {
      setMatches(ms);
      const predMap = new Map<string, FullMatchPrediction>();
      const promises = ms
        .filter((m) => m.status !== "scheduled")
        .slice(0, 100)
        .map(async (m) => {
          try {
            const p = await api.matches.predict(m.id);
            predMap.set(m.id, p);
          } catch { /* prediction not available */ }
        });
      await Promise.allSettled(promises);
      setPredictions(predMap);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const byStage = useMemo(() => {
    const map: Record<string, Match[]> = {};
    matches.forEach((m) => {
      if (!map[m.stage]) map[m.stage] = [];
      map[m.stage].push(m);
    });
    return map;
  }, [matches]);

  if (loading) return <SkeletonPage />;

  const toggleMatch = (id: string) => {
    setExpandedMatches((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const stageOrder = ["group_stage", "round_of_32", "round_of_16", "quarter_final", "semi_final", "third_place", "final"];

  return (
    <div className="container-page space-y-6">
      <div>
        <h1 className="page-title">Matches</h1>
        <p className="page-subtitle">All 104 tournament fixtures with live predictions.</p>
      </div>

      {stageOrder.filter((s) => byStage[s]).map((stage) => {
        const stageMatches = byStage[stage];
        const isExpanded = expandedStage === stage || expandedStage === null;
        return (
          <div key={stage}>
            <button
              onClick={() => setExpandedStage(expandedStage === stage ? null : stage)}
              className="flex items-center gap-2 text-sm font-semibold text-[hsl(var(--foreground))] mb-3 hover:text-primary-600 transition-colors"
            >
              {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              {getStageLabel(stage)}
              <span className="text-xs font-normal text-[hsl(var(--muted))]">({stageMatches.length})</span>
            </button>
            {isExpanded && (
              <div className="space-y-3 mb-6">
                {stageMatches.map((m) => {
                  const pred = predictions.get(m.id);
                  return (
                    <Card key={m.id} className="overflow-hidden">
                      <CardContent className="p-0">
                        <button
                          onClick={() => pred && toggleMatch(m.id)}
                          className="w-full text-left p-4 flex items-center gap-4 hover:bg-gray-50/50 transition-colors"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 text-xs text-[hsl(var(--muted))] mb-2">
                              {formatDate(m.match_date)}
                              {m.group_name && <><span>&middot;</span><Badge variant="default">Group {m.group_name}</Badge></>}
                              <Badge variant={m.status === "finished" ? "success" : m.status === "live" ? "warning" : "default"}>
                                {m.status}
                              </Badge>
                            </div>
                            {pred ? (
                              <ProbabilityBar
                                homeWin={pred.home_win_prob}
                                draw={pred.draw_prob}
                                awayWin={pred.away_win_prob}
                                homeLabel={pred.home_team}
                                awayLabel={pred.away_team}
                                height={28}
                              />
                            ) : (
                              <div className="flex items-center justify-between text-sm font-medium">
                                <span className="text-blue-600">{m.home_team_id}</span>
                                <span className="mx-4 font-bold text-gray-900">
                                  {m.home_goals !== null ? `${m.home_goals} - ${m.away_goals}` : "vs"}
                                </span>
                                <span className="text-red-600">{m.away_team_id}</span>
                              </div>
                            )}
                          </div>
                          {pred && (
                            <div className="flex flex-col items-end gap-1 text-xs text-[hsl(var(--muted))] min-w-[80px]">
                              {pred.confidence_index !== null && (
                                <Badge className={getConfidenceColor(pred.confidence_index)}>
                                  {getConfidenceLabel(pred.confidence_index)}
                                </Badge>
                              )}
                              {pred.most_likely_score && (
                                <span className="font-mono text-xs text-gray-500">
                                  {pred.most_likely_score}
                                </span>
                              )}
                              <ChevronRight className="w-3 h-3" />
                            </div>
                          )}
                        </button>
                        {pred && expandedMatches.has(m.id) && (
                          <div className="px-4 pb-4 pt-2 border-t border-[hsl(var(--border))] bg-gray-50/50">
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                              {[
                                { label: "BTTS", value: `${(pred.btts_prob * 100).toFixed(0)}%`, icon: Target },
                                { label: "Over 2.5", value: `${(pred.over_25_prob * 100).toFixed(0)}%`, icon: BarChart3 },
                                { label: "Over 3.5", value: `${(pred.over_35_prob * 100).toFixed(0)}%`, icon: BarChart3 },
                                { label: "Surprise Risk", value: `${(pred.surprise_risk * 100).toFixed(0)}%`, icon: AlertTriangle },
                                { label: `${pred.home_team} CS`, value: `${(pred.home_clean_sheet * 100).toFixed(0)}%`, icon: Activity },
                                { label: `${pred.away_team} CS`, value: `${(pred.away_clean_sheet * 100).toFixed(0)}%`, icon: Activity },
                              ].map((s) => (
                                <div key={s.label} className="panel p-2">
                                  <div className="text-2xs text-[hsl(var(--muted))]">{s.label}</div>
                                  <div className="text-sm font-bold font-mono">{s.value}</div>
                                </div>
                              ))}
                            </div>
                            {pred.top_10_scores && pred.top_10_scores.length > 0 && (
                              <div className="mt-3 flex flex-wrap gap-1.5">
                                {pred.top_10_scores.slice(0, 5).map(([score, prob]) => (
                                  <span key={score} className="px-2 py-0.5 text-xs bg-white rounded-md border border-[hsl(var(--border))] font-mono">
                                    {score}: {(prob * 100).toFixed(1)}%
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
