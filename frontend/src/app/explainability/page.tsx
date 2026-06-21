"use client";

import { useEffect, useState, useMemo } from "react";
import { api, CalibrationReport, RefinementReport, CalibrationBin } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import CalibrationCurveChart from "@/components/CalibrationCurveChart";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend,
} from "recharts";
import {
  BrainCircuit, TrendingUp, Shield, AlertTriangle,
  Activity, Lightbulb, ArrowUpRight,
} from "lucide-react";

export default function ExplainabilityPage() {
  const [calibration, setCalibration] = useState<CalibrationReport | null>(null);
  const [refinement, setRefinement] = useState<RefinementReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.calibration.results()
      .then(setCalibration)
      .catch(() => {})
      .finally(() => {
        api.refinement.results()
          .then(setRefinement)
          .catch(() => {})
          .finally(() => setLoading(false));
      });
  }, []);

  const runAnalysis = async () => {
    setRunning(true);
    try {
      const cal = await api.calibration.run();
      setCalibration(cal);
      const ref = await api.refinement.run();
      setRefinement(ref);
    } catch { /* ignore */ }
    setRunning(false);
  };

  if (loading) return <SkeletonPage />;

  return (
    <div className="container-page space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">Transparency</div>
          <h1 className="page-title">Model Explainability</h1>
          <p className="page-subtitle">Calibration curves, SHAP-style feature importance, and prediction breakdowns.</p>
        </div>
        <button
          onClick={runAnalysis}
          disabled={running}
          className="px-3 py-1.5 text-xs font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          {running ? "Running..." : "Run Analysis"}
        </button>
      </div>

      {!calibration && !refinement && (
        <Card>
          <CardContent className="p-8 text-center text-[hsl(var(--muted))]">
            <BrainCircuit className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No analysis data available. Click &ldquo;Run Analysis&rdquo; to generate calibration and refinement reports.</p>
          </CardContent>
        </Card>
      )}

      {calibration && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Brier Score", value: calibration.overall.brier_score.toFixed(4), color: calibration.overall.brier_score < 0.2 ? "ok" : calibration.overall.brier_score < 0.3 ? "warn" : "bad" },
              { label: "Log Loss", value: calibration.overall.log_loss.toFixed(4), color: "ok" },
              { label: "Accuracy", value: `${(calibration.overall.accuracy * 100).toFixed(1)}%`, color: calibration.overall.accuracy > 0.6 ? "ok" : "warn" },
              { label: "ECE", value: `${(calibration.overall.calibration_error * 100).toFixed(2)}%`, color: calibration.overall.calibration_error < 0.05 ? "ok" : calibration.overall.calibration_error < 0.1 ? "warn" : "bad" },
            ].map((s) => (
              <Card key={s.label}>
                <CardContent className="p-4 text-center">
                  <div className="stat-value text-lg">{s.value}</div>
                  <div className="stat-label text-xs">{s.label}</div>
                  <Badge className={s.color === "ok" ? "bg-green-100 text-green-700" : s.color === "warn" ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-700"}>
                    {s.color === "ok" ? "Good" : s.color === "warn" ? "Fair" : "Poor"}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>

          {calibration.calibration_curve.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Activity className="w-4 h-4 text-blue-500" />
                  Calibration Curve — Predicted vs Actual
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CalibrationCurveChart curve={calibration.calibration_curve} />
              </CardContent>
            </Card>
          )}

          {calibration.outcome_curves && calibration.outcome_curves.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {calibration.outcome_curves.map((oc) => (
                <Card key={oc.outcome}>
                  <CardHeader>
                    <CardTitle className="text-xs">{oc.outcome.replace(/_/g, " ")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="h-48">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={oc.bins.map((b) => ({
                          bin: `${(b.bin_lower * 100).toFixed(0)}-${(b.bin_upper * 100).toFixed(0)}%`,
                          predicted: +(b.mean_predicted * 100).toFixed(1),
                          actual: +(b.mean_actual * 100).toFixed(1),
                        }))} margin={{ top: 8, right: 8, left: -8, bottom: 4 }}>
                          <XAxis dataKey="bin" tick={{ fontSize: 9 }} />
                          <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}%`} domain={[0, 100]} />
                          <Tooltip />
                          <Legend wrapperStyle={{ fontSize: 10 }} />
                          <Bar dataKey="predicted" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={20} name="Predicted" />
                          <Bar dataKey="actual" fill="#22c55e" radius={[4, 4, 0, 0]} maxBarSize={20} name="Actual" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {calibration.bias && Object.keys(calibration.bias).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <AlertTriangle className="w-4 h-4 text-yellow-500" />
                  Prediction Biases
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={Object.entries(calibration.bias).map(([k, v]) => ({ name: k, bias: v * 100 }))} layout="vertical" margin={{ left: 100 }}>
                      <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v.toFixed(0)}%`} />
                      <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(v: any) => `${Number(v).toFixed(1)}%`} />
                      <Bar dataKey="bias" radius={[0, 4, 4, 0]}>
                        {Object.entries(calibration.bias).map((_, i) => (
                          <Cell key={i} fill={Object.values(calibration.bias)[i] > 0 ? "#ef4444" : "#22c55e"} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {refinement && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Lightbulb className="w-4 h-4 text-yellow-500" />
              Recommendation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-[hsl(var(--foreground))]">{refinement.recommendation}</p>
            <div className="mt-3 flex items-center gap-2">
              <Badge className="bg-green-100 text-green-700">Best: {refinement.best_method}</Badge>
              <span className="text-xs text-[hsl(var(--muted))]">
                Brier from {refinement.benchmark_before?.overall?.brier_score?.toFixed(4) || "?"} to {refinement.benchmark_after?.overall?.brier_score?.toFixed(4) || "?"}
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
