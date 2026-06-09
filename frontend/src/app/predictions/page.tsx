"use client";

import { useEffect, useState } from "react";
import { api, MatchPrediction } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatProbability } from "@/lib/utils";

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<MatchPrediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.predictions.list().then(setPredictions).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="container-page">
      <h1 className="page-title">Match Predictions</h1>
      <p className="page-subtitle mb-6">
        Poisson-based match outcome probabilities. Shows home win, draw, and away win likelihoods.
      </p>

      {loading ? (
        <p className="text-gray-500">Loading predictions...</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {predictions.map((p) => (
            <Card key={p.match_id}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">
                  {p.home_team} vs {p.away_team}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-3">
                  <div className="flex justify-between text-sm">
                    <span>{p.home_team}</span>
                    <span className="font-bold text-green-600">
                      {formatProbability(p.home_win_prob)}
                    </span>
                  </div>
                  <div className="mt-1 flex justify-between text-sm">
                    <span>Draw</span>
                    <span className="font-bold text-gray-600">
                      {formatProbability(p.draw_prob)}
                    </span>
                  </div>
                  <div className="mt-1 flex justify-between text-sm">
                    <span>{p.away_team}</span>
                    <span className="font-bold text-red-600">
                      {formatProbability(p.away_win_prob)}
                    </span>
                  </div>
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>xG: {p.home_expected_goals.toFixed(2)} - {p.away_expected_goals.toFixed(2)}</span>
                  {p.most_likely_score && (
                    <Badge>{p.most_likely_score}</Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
