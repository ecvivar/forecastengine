"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SkeletonPage } from "@/components/ui/skeleton";
import {
  api,
  type RefinementReport,
  type ReliabilityCurve,
  type CalibrationMethod,
  type BenchmarkEntry,
  type CalibrationReport,
} from "@/lib/api";
import ReliabilityDiagram from "@/components/ReliabilityDiagram";
import BenchmarkChart from "@/components/BenchmarkChart";
import CalibrationCurveChart from "@/components/CalibrationCurveChart";
import { BarChart3, CheckCircle2, AlertTriangle } from "lucide-react";

export default function CalibrationPage() {
  const [report, setReport] = useState<RefinementReport | null>(null);
  const [calibReport, setCalibReport] = useState<CalibrationReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.refinement.run(),
      api.calibration.run("full").catch(() => null),
    ])
      .then(([ref, cal]) => {
        setReport(ref);
        setCalibReport(cal);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <SkeletonPage />;

  if (error || !report) {
    return (
      <div className="container-page text-center py-12">
        <AlertTriangle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">Calibration Data Unavailable</h2>
        <p className="text-gray-500">{error || "Failed to load calibration report."}</p>
      </div>
    );
  }

  const bc = report.benchmark_before;
  const getMetric = (m: string) => {
    const entry = bc[m as keyof typeof bc] as BenchmarkEntry | undefined;
    return entry ? { brier: entry.brier_score, ece: entry.ece, acc: entry.accuracy } : null;
  };

  const fullMetrics = getMetric("full");
  const dcMetrics = getMetric("dixon_coles");
  const eloMetrics = getMetric("elo");

  return (
    <div className="container-page space-y-6">
      <div>
        <div className="text-xs text-[hsl(var(--muted))] uppercase tracking-wider mb-1">Accuracy</div>
        <h1 className="page-title">Calibration Dashboard</h1>
        <p className="page-subtitle">Brier score, ECE, calibration curves, and confederation bias tracking.</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-primary-600">
              {fullMetrics?.brier.toFixed(4) || "—"}
            </div>
            <div className="text-xs text-gray-500">Full Model Brier (↓)</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {fullMetrics ? (fullMetrics.ece * 100).toFixed(2) + "%" : "—"}
            </div>
            <div className="text-xs text-gray-500">ECE (↓)</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">
              {fullMetrics ? (fullMetrics.acc * 100).toFixed(1) + "%" : "—"}
            </div>
            <div className="text-xs text-gray-500">Accuracy (↑)</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">
              <Badge
                variant={
                  report.best_method === "none (uncalibrated)"
                    ? "success"
                    : "warning"
                }
                className="text-sm"
              >
                {report.best_method === "none (uncalibrated)"
                  ? "No Calibration Needed"
                  : report.best_method}
              </Badge>
            </div>
            <div className="text-xs text-gray-500">Best Calibration</div>
          </CardContent>
        </Card>
      </div>

      {/* Calibration Curve */}
      {calibReport && calibReport.calibration_curve && calibReport.calibration_curve.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Calibration Curve — Full Model</CardTitle>
          </CardHeader>
          <CardContent>
            <CalibrationCurveChart curve={calibReport.calibration_curve} />
          </CardContent>
        </Card>
      )}

      {/* Benchmark Before/After */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Benchmark — Brier Score</CardTitle>
          </CardHeader>
          <CardContent>
            <BenchmarkChart
              before={report.benchmark_before}
              after={report.benchmark_after}
              metric="brier_score"
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Benchmark — ECE</CardTitle>
          </CardHeader>
          <CardContent>
            <BenchmarkChart
              before={report.benchmark_before}
              after={report.benchmark_after}
              metric="ece"
            />
          </CardContent>
        </Card>
      </div>

      {/* Model comparison table */}
      <Card>
        <CardHeader>
          <CardTitle>Model Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-gray-500 text-xs uppercase">
                  <th className="text-left py-2">Model</th>
                  <th className="text-center py-2">Brier Score</th>
                  <th className="text-center py-2">Log Loss</th>
                  <th className="text-center py-2">Accuracy</th>
                  <th className="text-center py-2">ECE</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(report.benchmark_before).map(
                  ([name, metrics]) => (
                    <tr
                      key={name}
                      className={`border-b border-gray-50 hover:bg-gray-50 ${
                        name === "full" ? "bg-blue-50 font-medium" : ""
                      }`}
                    >
                      <td className="py-2 capitalize">
                        {name.replace(/_/g, " ")}
                      </td>
                      <td className="text-center py-2">{metrics.brier_score.toFixed(4)}</td>
                      <td className="text-center py-2">{metrics.log_loss.toFixed(4)}</td>
                      <td className="text-center py-2">
                        {(metrics.accuracy * 100).toFixed(2)}%
                      </td>
                      <td className="text-center py-2">
                        {(metrics.ece * 100).toFixed(2)}%
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Calibration Methods */}
      <Card>
        <CardHeader>
          <CardTitle>Calibration Methods Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-gray-500 text-xs uppercase">
                  <th className="text-left py-2">Method</th>
                  <th className="text-center py-2">Brier</th>
                  <th className="text-center py-2">Log Loss</th>
                  <th className="text-center py-2">Accuracy</th>
                  <th className="text-center py-2">ECE</th>
                  <th className="text-center py-2">Best?</th>
                </tr>
              </thead>
              <tbody>
                {report.calibration_methods.map((cm) => (
                  <tr
                    key={cm.method_name}
                    className={`border-b border-gray-50 hover:bg-gray-50 ${
                      cm.method_name === report.best_method
                        ? "bg-green-50 font-medium"
                        : ""
                    }`}
                  >
                    <td className="py-2 capitalize">
                      {cm.method_name.replace(/_/g, " ")}
                    </td>
                    <td className="text-center py-2">{cm.brier_score.toFixed(4)}</td>
                    <td className="text-center py-2">{cm.log_loss.toFixed(4)}</td>
                    <td className="text-center py-2">
                      {(cm.accuracy * 100).toFixed(2)}%
                    </td>
                    <td className="text-center py-2">
                      {(cm.ece * 100).toFixed(2)}%
                    </td>
                    <td className="text-center py-2">
                      {cm.method_name === report.best_method ? (
                        <CheckCircle2 className="w-4 h-4 text-green-600 mx-auto" />
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Reliability Diagrams */}
      <Card>
        <CardHeader>
          <CardTitle>Reliability Diagrams</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {report.reliability_curves.map((curve) => (
              <ReliabilityDiagram
                key={curve.outcome}
                curve={curve}
                title={
                  curve.outcome === "max_confidence"
                    ? "Max Confidence"
                    : curve.outcome.charAt(0).toUpperCase() + curve.outcome.slice(1)
                }
              />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Bias Reduction */}
      <Card>
        <CardHeader>
          <CardTitle>Bias Reduction Results</CardTitle>
        </CardHeader>
        <CardContent>
          {report.bias_reductions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-gray-500 text-xs uppercase">
                    <th className="text-left py-2">Adjustment</th>
                    <th className="text-center py-2">Before Brier</th>
                    <th className="text-center py-2">After Brier</th>
                    <th className="text-center py-2">Improvement</th>
                    <th className="text-center py-2">Applied?</th>
                  </tr>
                </thead>
                <tbody>
                  {report.bias_reductions.map((br, i) => (
                    <tr
                      key={i}
                      className={`border-b border-gray-50 hover:bg-gray-50 ${
                        br.applied ? "bg-green-50" : ""
                      }`}
                    >
                      <td className="py-2 font-medium">{br.adjustment_name}</td>
                      <td className="text-center py-2">{br.before_metric.toFixed(4)}</td>
                      <td className="text-center py-2">{br.after_metric.toFixed(4)}</td>
                      <td className="text-center py-2">
                        <span
                          className={
                            br.improvement > 0
                              ? "text-green-600"
                              : "text-gray-400"
                          }
                        >
                          {br.improvement > 0 ? "+" : ""}
                          {br.improvement.toFixed(2)}%
                        </span>
                      </td>
                      <td className="text-center py-2">
                        {br.applied ? (
                          <Badge variant="success">Yes</Badge>
                        ) : (
                          <Badge variant="default">No</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-sm text-gray-400 italic py-4 text-center">
              No bias reduction data available.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recommendation */}
      <Card className="border-2 border-primary-200 bg-primary-50">
        <CardContent className="p-6">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="w-6 h-6 text-primary-700 mt-1 shrink-0" />
            <div>
              <h3 className="font-bold text-primary-800 mb-1">Recommendation</h3>
              <p className="text-sm text-primary-700">{report.recommendation}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
