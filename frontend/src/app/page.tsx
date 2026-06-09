"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api, IGFScore, Simulation } from "@/lib/api";
import { formatProbability } from "@/lib/utils";

export default function HomePage() {
  const [rankings, setRankings] = useState<IGFScore[]>([]);
  const [simulations, setSimulations] = useState<Simulation[]>([]);

  useEffect(() => {
    api.rankings.igf().then(setRankings).catch(() => {});
    api.simulations.list().then(setSimulations).catch(() => {});
  }, []);

  const topTeams = rankings.slice(0, 5);

  return (
    <div className="container-page">
      <div className="mb-8">
        <h1 className="page-title">WorldCup Forecast Engine 2026</h1>
        <p className="page-subtitle">
          Monte Carlo simulation platform for the FIFA World Cup 2026.
          Predict match outcomes, group standings, and tournament champions.
        </p>
      </div>

      <div className="mb-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Teams</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-primary-600">48</p>
            <p className="text-sm text-gray-500">Participating nations</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Groups</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-primary-600">12</p>
            <p className="text-sm text-gray-500">Group stage groups</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Matches</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-primary-600">104</p>
            <p className="text-sm text-gray-500">Total tournament matches</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Simulations</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-primary-600">100k+</p>
            <p className="text-sm text-gray-500">Monte Carlo runs</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Top Teams (IGF)</CardTitle>
            <Link href="/rankings">
              <Button variant="ghost" size="sm">View all</Button>
            </Link>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2 font-medium">Rank</th>
                  <th className="pb-2 font-medium">Team</th>
                  <th className="pb-2 font-medium text-right">IGF Score</th>
                </tr>
              </thead>
              <tbody>
                {topTeams.map((t, i) => (
                  <tr key={t.team_id} className="border-b last:border-0">
                    <td className="py-2 text-gray-500">{i + 1}</td>
                    <td className="py-2 font-medium">{t.team_name}</td>
                    <td className="py-2 text-right font-mono">
                      {t.igf_score.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Simulations</CardTitle>
            <Link href="/simulations">
              <Button variant="ghost" size="sm">View all</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {simulations.length === 0 ? (
              <p className="text-sm text-gray-500">
                No simulations yet. Run one to see results.
              </p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-2 font-medium">Name</th>
                    <th className="pb-2 font-medium">Runs</th>
                    <th className="pb-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {simulations.slice(0, 5).map((s) => (
                    <tr key={s.id} className="border-b last:border-0">
                      <td className="py-2">{s.name || "Unnamed"}</td>
                      <td className="py-2 font-mono">
                        {s.num_simulations.toLocaleString()}
                      </td>
                      <td className="py-2">
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                            s.status === "completed"
                              ? "bg-green-100 text-green-800"
                              : s.status === "running"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
