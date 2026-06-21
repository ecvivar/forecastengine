"use client";

import { useEffect, useState } from "react";
import { api, Simulation, SimulationDetail } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { formatDateTime } from "@/lib/utils";
import {
  Clock, RefreshCw, CheckCircle, Play, ChevronDown, ChevronRight,
} from "lucide-react";

interface ChangelogEntry {
  version: string;
  date: string;
  title: string;
  description: string;
  type: "release" | "sprint" | "hotfix";
}

const CHANGELOG: ChangelogEntry[] = [
  { version: "v1.0", date: "2026-06-01", title: "Initial Release", description: "Full tournament simulation with Monte Carlo (10K runs), calibration v3, ELO/IGF ranking, and World Cup 2026 fixture support.", type: "release" },
  { version: "Sprint 10", date: "2026-06-15", title: "Command Center UI", description: "Frontend redesign with dashboard, team detail pages, comparison tool, explainability panel, and monitoring dashboard.", type: "sprint" },
  { version: "Sprint 9.5", date: "2026-05-25", title: "Production Hardening", description: "Audit trail, model registry, calibration tracking, drift detection, and reality-based recalibration simulator.", type: "sprint" },
  { version: "Sprint 9", date: "2026-05-10", title: "Scientific Reliability", description: "Calibration v3 with Platt scaling, isotonic regression, beta calibration; 90/100 World Cup Readiness Score.", type: "sprint" },
  { version: "Sprint 8.5", date: "2026-04-20", title: "Data Quality & Coverage", description: "Data quality pipeline, missing value imputation, outlier detection, tournament coverage expansion.", type: "sprint" },
  { version: "Sprint 8", date: "2026-04-01", title: "Historical Simulation & Calibration v2", description: "10K Monte Carlo pipeline, historical backtesting, calibration v2 with temperature scaling.", type: "sprint" },
];

export default function HistoryPage() {
  const [simulations, setSimulations] = useState<Simulation[]>([]);
  const [selectedSim, setSelectedSim] = useState<SimulationDetail | null>(null);
  const [expandedSim, setExpandedSim] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.simulations.list()
      .then(setSimulations)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const loadSimDetail = async (id: string) => {
    if (expandedSim === id) {
      setExpandedSim(null);
      setSelectedSim(null);
      return;
    }
    setExpandedSim(id);
    try {
      const detail = await api.simulations.get(id);
      setSelectedSim(detail);
    } catch {
      setSelectedSim(null);
    }
  };

  if (loading) return <SkeletonPage />;

  const sortedSims = [...simulations].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div className="container-page space-y-6">
      <div>
        <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">Timeline</div>
        <h1 className="page-title">History</h1>
        <p className="page-subtitle">Versioned predictions, simulation runs, and development milestones.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Clock className="w-4 h-4 text-blue-500" />
            Development Milestones
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-px bg-[hsl(var(--border))]" />
            <div className="space-y-6">
              {CHANGELOG.map((entry) => (
                <div key={entry.version} className="relative pl-10">
                  <div className={`absolute left-2.5 w-3 h-3 rounded-full border-2 border-white ${
                    entry.type === "release" ? "bg-green-500" : entry.type === "sprint" ? "bg-blue-500" : "bg-yellow-500"
                  }`} style={{ top: 4 }} />
                  <div className="flex items-center gap-2 mb-1">
                    <Badge className={entry.type === "release" ? "bg-green-100 text-green-700" : entry.type === "sprint" ? "bg-blue-100 text-blue-700" : "bg-yellow-100 text-yellow-700"}>
                      {entry.version}
                    </Badge>
                    <span className="text-xs text-[hsl(var(--muted))]">{entry.date}</span>
                  </div>
                  <p className="text-sm font-medium">{entry.title}</p>
                  <p className="text-xs text-[hsl(var(--muted))] mt-0.5">{entry.description}</p>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <RefreshCw className="w-4 h-4 text-purple-500" />
            Simulation Runs
          </CardTitle>
        </CardHeader>
        <CardContent>
          {sortedSims.length > 0 ? (
            <div className="space-y-2">
              {sortedSims.map((sim) => (
                <div key={sim.id}>
                  <button
                    onClick={() => loadSimDetail(sim.id)}
                    className="w-full text-left flex items-center gap-3 py-3 px-3 rounded-lg hover:bg-gray-50 transition-colors border border-[hsl(var(--border))]"
                  >
                    {expandedSim === sim.id ? <ChevronDown className="w-4 h-4 text-[hsl(var(--muted))]" /> : <ChevronRight className="w-4 h-4 text-[hsl(var(--muted))]" />}
                    {sim.status === "completed" ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : sim.status === "running" ? (
                      <RefreshCw className="w-4 h-4 text-yellow-500 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4 text-gray-400" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate">{sim.name || `Simulation ${sim.id.slice(0, 8)}`}</span>
                        <Badge variant="default" className="text-2xs">{sim.num_simulations.toLocaleString()} runs</Badge>
                      </div>
                      <div className="text-xs text-[hsl(var(--muted))]">
                        Created: {formatDateTime(sim.created_at)}
                        {sim.completed_at && <> &middot; Completed: {formatDateTime(sim.completed_at)}</>}
                      </div>
                    </div>
                    <Badge className={
                      sim.status === "completed" ? "bg-green-100 text-green-700" :
                      sim.status === "running" ? "bg-yellow-100 text-yellow-700" :
                      "bg-gray-100 text-gray-700"
                    }>
                      {sim.status}
                    </Badge>
                  </button>
                  {expandedSim === sim.id && selectedSim && selectedSim.results && (
                    <div className="ml-6 mt-2 p-3 bg-gray-50 rounded-lg border border-[hsl(var(--border))]">
                      <div className="text-xs font-semibold text-[hsl(var(--muted))] mb-2 uppercase tracking-wider">Top Results</div>
                      <div className="space-y-1">
                        {selectedSim.results
                          .sort((a, b) => b.won_tournament - a.won_tournament)
                          .slice(0, 10)
                          .map((r, i) => (
                            <div key={r.team_id} className="flex items-center gap-2 text-sm py-1 border-b border-gray-100 last:border-0">
                              <span className="w-4 text-xs text-[hsl(var(--muted))]">{i + 1}</span>
                              <span className="flex-1 truncate">{r.team_name}</span>
                              <span className="text-xs font-mono text-yellow-600">W:{r.won_tournament}</span>
                              <span className="text-xs font-mono text-blue-600">F:{r.reached_final}</span>
                              <span className="text-xs font-mono text-green-600">SF:{r.reached_semi_final}</span>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-[hsl(var(--muted))] italic py-4 text-center">
              No simulation runs found. Create a simulation via the API to see results here.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
