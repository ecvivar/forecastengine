"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, type FullMatchPrediction } from "@/lib/api";
import {
  formatPercent,
  getConfidenceLabel,
  getStageLabel,
} from "@/lib/utils";
import ProbabilityBar from "@/components/ProbabilityBar";
import ConfidenceGauge from "@/components/ConfidenceGauge";
import ScorelineChart from "@/components/ScorelineChart";
import { ArrowLeft, AlertTriangle } from "lucide-react";
import Link from "next/link";

export default function MatchPredictionDetailPage() {
  const params = useParams();
  const matchId = params.id as string;

  const [pred, setPred] = useState<FullMatchPrediction | null>(null);
  const [match, setMatch] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!matchId) return;
    Promise.all([
      api.predictions.full(matchId).catch(() => null),
      api.matches.get(matchId).catch(() => null),
    ])
      .then(([p, m]) => {
        setPred(p);
        setMatch(m);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [matchId]);

  if (loading) {
    return (
      <div className="container-page">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      </div>
    );
  }

  if (error || !pred) {
    return (
      <div className="container-page text-center py-12">
        <AlertTriangle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">Prediction Not Available</h2>
        <p className="text-gray-500">{error || "Match not found or no prediction data."}</p>
        <Link href="/predictions" className="text-primary-600 hover:underline mt-4 inline-block">
          ← All Predictions
        </Link>
      </div>
    );
  }

  const bettingMarkets = [
    { label: "BTTS Yes", value: pred.btts_prob },
    { label: "BTTS No", value: 1 - pred.btts_prob },
    { label: "Over 2.5", value: pred.over_25_prob },
    { label: "Under 2.5", value: pred.under_25_prob },
    { label: "Over 3.5", value: pred.over_35_prob },
    { label: "Home CS", value: pred.home_clean_sheet },
    { label: "Away CS", value: pred.away_clean_sheet },
  ];

  return (
    <div className="container-page space-y-6">
      <Link
        href="/predictions"
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-primary-600"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Predictions
      </Link>

      {/* Match Header */}
      <Card>
        <CardContent className="p-8">
          <div className="flex items-center justify-between mb-4">
            <Badge variant="info">{getStageLabel(match?.stage || "?")}</Badge>
            {pred.confidence_level && (
              <Badge variant={pred.confidence_index >= 65 ? "success" : "warning"}>
                {pred.confidence_level}
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-4 items-center">
            <div className="text-right">
              <div className="text-2xl font-bold">{pred.home_team}</div>
              <div className="text-sm text-gray-400 mt-1">
                xG: {pred.home_expected_goals.toFixed(2)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold text-primary-600">
                {pred.most_likely_score || "?-?"}
              </div>
              <div className="text-xs text-gray-400 mt-1">Most Likely Score</div>
            </div>
            <div className="text-left">
              <div className="text-2xl font-bold">{pred.away_team}</div>
              <div className="text-sm text-gray-400 mt-1">
                xG: {pred.away_expected_goals.toFixed(2)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main prediction grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Outcome Probabilities */}
        <Card>
          <CardHeader>
            <CardTitle>Outcome Probabilities</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ProbabilityBar
              homeWin={pred.home_win_prob}
              draw={pred.draw_prob}
              awayWin={pred.away_win_prob}
              homeLabel={pred.home_team}
              awayLabel={pred.away_team}
              height={32}
            />
            <div className="grid grid-cols-3 gap-4 text-center mt-4">
              <div className="bg-blue-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-blue-600">
                  {formatPercent(pred.home_win_prob)}
                </div>
                <div className="text-xs text-gray-500">{pred.home_team}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-gray-600">
                  {formatPercent(pred.draw_prob)}
                </div>
                <div className="text-xs text-gray-500">Draw</div>
              </div>
              <div className="bg-red-50 rounded-lg p-3">
                <div className="text-2xl font-bold text-red-600">
                  {formatPercent(pred.away_win_prob)}
                </div>
                <div className="text-xs text-gray-500">{pred.away_team}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Confidence & Surprise */}
        <Card>
          <CardHeader>
            <CardTitle>Confidence &amp; Risk Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-around mb-6">
              <div className="text-center">
                <ConfidenceGauge
                  value={pred.confidence_index}
                  label="Confidence Index"
                  size="lg"
                />
              </div>
              <div className="text-center">
                <div className="w-24 h-24 rounded-full border-4 border-orange-200 flex items-center justify-center mx-auto">
                  <div>
                    <div className="text-2xl font-bold text-orange-600">
                      {(pred.surprise_risk * 100).toFixed(0)}
                    </div>
                    <div className="text-[10px] text-gray-400">%</div>
                  </div>
                </div>
                <div className="text-xs text-gray-500 mt-1">Surprise Risk</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-gray-50 rounded-lg p-2 text-center">
                <span className="text-gray-400">Level</span>
                <div className="font-bold">{getConfidenceLabel(pred.confidence_index)}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-2 text-center">
                <span className="text-gray-400">Most Likely</span>
                <div className="font-bold">{pred.most_likely_score || "?"}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Top 10 Scorelines */}
        <Card>
          <CardHeader>
            <CardTitle>Top 10 Most Likely Scores</CardTitle>
          </CardHeader>
          <CardContent>
            <ScorelineChart scores={pred.top_10_scores} />
            <div className="grid grid-cols-5 gap-1 mt-3">
              {(pred.top_10_scores || []).slice(0, 10).map(([score, prob]) => (
                <div
                  key={score}
                  className="text-center bg-gray-50 rounded p-1"
                >
                  <div className="text-sm font-bold">{score}</div>
                  <div className="text-[10px] text-gray-400">
                    {(prob * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Betting Markets */}
        <Card>
          <CardHeader>
            <CardTitle>Betting Markets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {bettingMarkets.map((bm) => (
                <div key={bm.label} className="flex items-center gap-3">
                  <span className="text-sm w-28">{bm.label}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-4">
                    <div
                      className={`h-4 rounded-full transition-all ${
                        bm.value >= 0.5
                          ? "bg-green-500"
                          : "bg-gray-300"
                      }`}
                      style={{ width: `${(bm.value * 100).toFixed(0)}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold w-14 text-right">
                    {formatPercent(bm.value)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
