"use client";

import { useEffect, useState, useMemo } from "react";
import { api, CalibrationReport, AuditEntry, DriftReport } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import { formatDateTime } from "@/lib/utils";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine,
} from "recharts";
import {
  Activity, Shield, AlertTriangle, CheckCircle,
  Clock, Database, RefreshCw, BarChart3,
} from "lucide-react";

export default function MonitoringPage() {
  const [calibration, setCalibration] = useState<CalibrationReport | null>(null);
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [drift, setDrift] = useState<DriftReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.calibration.results().catch(() => null),
      api.audit.log().catch(() => [] as AuditEntry[]),
      api.monitoring.drift().catch(() => null),
    ]).then(([cal, audit, driftReport]) => {
      setCalibration(cal);
      setAuditLog(Array.isArray(audit) ? audit : []);
      setDrift(driftReport);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonPage />;

  const metrics = [
    { label: "Calibration Status", value: calibration ? "Active" : "Pending", icon: CheckCircle, color: calibration ? "ok" : "warn" },
    { label: "Drift Detected", value: drift?.has_drift ? "Yes" : "No", icon: drift?.has_drift ? AlertTriangle : Shield, color: drift?.has_drift ? "bad" : "ok" },
    { label: "Audit Entries", value: auditLog.length.toString(), icon: Database, color: "ok" },
    { label: "Model Version", value: calibration ? "Sprint 9" : "—", icon: Activity, color: "ok" },
  ];

  return (
    <div className="container-page space-y-6">
      <div>
        <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">Observability</div>
        <h1 className="page-title">Monitoring</h1>
        <p className="page-subtitle">Calibration tracking, drift detection, and audit trail for the ForecastEngine.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {metrics.map((m) => (
          <Card key={m.label}>
            <CardContent className="p-4 flex items-center gap-3">
              <m.icon className={`w-5 h-5 ${m.color === "ok" ? "text-green-500" : m.color === "warn" ? "text-yellow-500" : "text-red-500"}`} />
              <div>
                <div className={`stat-value text-base ${m.color === "bad" ? "text-red-600" : ""}`}>{m.value}</div>
                <div className="stat-label text-xs">{m.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {calibration?.calibration_curve && calibration.calibration_curve.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="w-4 h-4 text-blue-500" />
              Calibration Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={calibration.calibration_curve.map((b) => ({
                  bin: `${(b.bin_lower * 100).toFixed(0)}%`,
                  predicted: +(b.mean_predicted * 100).toFixed(1),
                  actual: +(b.mean_actual * 100).toFixed(1),
                  count: b.count,
                }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="bin" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} domain={[0, 100]} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <ReferenceLine y={0} stroke="#e5e7eb" />
                  <Line type="monotone" dataKey="predicted" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} name="Predicted" />
                  <Line type="monotone" dataKey="actual" stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} name="Actual" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {drift && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <AlertTriangle className="w-4 h-4 text-yellow-500" />
              Drift Detection
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 mb-3">
              <Badge className={drift.has_drift ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}>
                {drift.has_drift ? "Drift Detected" : "Stable"}
              </Badge>
              <span className="text-xs text-[hsl(var(--muted))]">
                Score: {(drift.drift_score * 100).toFixed(1)}% &middot; Last checked: {drift.timestamp ? formatDateTime(drift.timestamp) : "—"}
              </span>
            </div>
            {drift.drifted_features.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {drift.drifted_features.map((f) => (
                  <Badge key={f} variant="danger" className="border border-red-200">{f}</Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Database className="w-4 h-4 text-purple-500" />
            Audit Log
          </CardTitle>
          <RefreshCw className="w-3 h-3 text-[hsl(var(--muted))]" />
        </CardHeader>
        <CardContent>
          {auditLog.length > 0 ? (
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
          ) : (
            <div className="text-sm text-[hsl(var(--muted))] italic py-4 text-center">
              No audit entries available. Run predictions to populate the audit log.
            </div>
          )}
        </CardContent>
      </Card>

      {calibration?.confederation_biases && calibration.confederation_biases.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <BarChart3 className="w-4 h-4 text-orange-500" />
              Confederation Bias
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {calibration.confederation_biases.map((cb) => (
                <div key={cb.confederation} className="panel p-3">
                  <div className="text-xs font-semibold mb-1">{cb.confederation}</div>
                  <div className="space-y-1 text-xs text-[hsl(var(--muted))]">
                    <div className="flex justify-between">
                      <span>Accuracy</span>
                      <span className="font-mono">{(cb.accuracy * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Brier</span>
                      <span className="font-mono">{cb.brier_score.toFixed(4)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Matches</span>
                      <span className="font-mono">{cb.match_count}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
