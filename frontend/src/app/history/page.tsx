"use client";

import { useEffect, useState } from "react";
import { api, Simulation, SimulationDetail, ModelVersion, CalibrationHistoryEntry, AuditEntry, DriftReport } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { formatDateTime } from "@/lib/utils";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import {
  Clock, RefreshCw, CheckCircle, Play, ChevronDown, ChevronRight,
  Activity, Database, AlertTriangle, BarChart3,
} from "lucide-react";

export default function HistoryPage() {
  const [simulations, setSimulations] = useState<Simulation[]>([]);
  const [selectedSim, setSelectedSim] = useState<SimulationDetail | null>(null);
  const [expandedSim, setExpandedSim] = useState<string | null>(null);
  const [modelVersions, setModelVersions] = useState<ModelVersion[]>([]);
  const [calHistory, setCalHistory] = useState<CalibrationHistoryEntry[]>([]);
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [drift, setDrift] = useState<DriftReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.simulations.list(),
      api.history.modelVersions().catch(() => [] as ModelVersion[]),
      api.history.calibration().catch(() => [] as CalibrationHistoryEntry[]),
      api.history.audit().catch(() => [] as AuditEntry[]),
      api.history.drift().catch(() => null),
    ])
      .then(([sims, versions, cal, audit, driftReport]) => {
        setSimulations(sims);
        setModelVersions(versions);
        setCalHistory(cal);
        setAuditLog(audit);
        setDrift(driftReport);
      })
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
        <p className="page-subtitle">Model versions, calibration tracking, audit trail, and simulation runs.</p>
      </div>

      {/* Model Versions */}
      {modelVersions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <BarChart3 className="w-4 h-4 text-blue-500" />
              Model Versions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[hsl(var(--muted))] text-xs border-b border-[hsl(var(--border))]">
                    <th className="pb-2 pr-3">Version</th>
                    <th className="pb-2 pr-3">Calibration</th>
                    <th className="pb-2 pr-3">Ensemble</th>
                    <th className="pb-2 pr-3">Active</th>
                    <th className="pb-2 pr-3">Registered</th>
                    <th className="pb-2">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {modelVersions.map((mv) => (
                    <tr key={mv.id} className="border-b border-[hsl(var(--border))] last:border-0">
                      <td className="py-2 pr-3 font-medium">{mv.sprint_version}</td>
                      <td className="py-2 pr-3 text-[hsl(var(--muted))]">{mv.calibration_version}</td>
                      <td className="py-2 pr-3 text-[hsl(var(--muted))]">{mv.ensemble_version}</td>
                      <td className="py-2 pr-3">{mv.active ? <Badge className="bg-green-100 text-green-700">Active</Badge> : "—"}</td>
                      <td className="py-2 pr-3 text-xs text-[hsl(var(--muted))]">{formatDateTime(mv.registered_at)}</td>
                      <td className="py-2 text-xs text-[hsl(var(--muted))]">{mv.description || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Calibration Trend */}
      {calHistory.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="w-4 h-4 text-green-500" />
              Calibration Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={calHistory.map((e) => ({
                  ts: formatDateTime(e.timestamp),
                  brier: +(e.brier * 100).toFixed(2),
                  accuracy: +(e.accuracy * 100).toFixed(1),
                  ece: +(e.ece * 100).toFixed(2),
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ts" tick={{ fontSize: 9 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="brier" stroke="#ef4444" strokeWidth={2} dot={false} name="Brier %" />
                  <Line type="monotone" dataKey="accuracy" stroke="#22c55e" strokeWidth={2} dot={false} name="Accuracy %" />
                  <Line type="monotone" dataKey="ece" stroke="#f59e0b" strokeWidth={2} dot={false} name="ECE %" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Drift Status */}
      {drift && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <AlertTriangle className="w-4 h-4 text-yellow-500" />
              Drift Detection
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 mb-2">
              <Badge className={drift.has_drift ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}>
                {drift.has_drift ? "Drift Detected" : "Stable"}
              </Badge>
              <span className="text-xs text-[hsl(var(--muted))]">
                Score: {(drift.drift_score * 100).toFixed(1)}% &middot; {formatDateTime(drift.timestamp)}
              </span>
            </div>
            {drift.drifted_features.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {drift.drifted_features.map((f) => (
                  <Badge key={f} variant="danger">{f}</Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Audit Log */}
      {auditLog.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Database className="w-4 h-4 text-purple-500" />
              Audit Log
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {auditLog.slice(0, 20).map((entry, i) => (
                <div key={entry.id || i} className="flex items-start gap-3 py-2 border-b border-[hsl(var(--border))] last:border-0 text-sm">
                  <Clock className="w-3 h-3 mt-0.5 text-[hsl(var(--muted))]" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <Badge variant="default" className="text-2xs">{String(entry.action || entry.home_team || "?")}</Badge>
                      <span className="text-xs text-[hsl(var(--muted))]">{formatDateTime(entry.timestamp)}</span>
                    </div>
                    <div className="text-xs mt-0.5 truncate">
                      {entry.details || `${entry.home_team || ""} vs ${entry.away_team || ""}`}
                    </div>
                  </div>
                  {entry.status && (
                    <Badge className={entry.status === "success" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}>
                      {entry.status}
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Simulation Runs */}
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
