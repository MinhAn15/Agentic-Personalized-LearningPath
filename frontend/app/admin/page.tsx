"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

// Types
interface Learner {
  id: string;
  name: string;
  cohort: 'TREATMENT' | 'CONTROL';
  progress: number;
  status: 'ACTIVE' | 'INACTIVE';
}

interface CohortStats {
  treatment: { count: number; avg_mastery: number; avg_time_spent_mins: number };
  control: { count: number; avg_mastery: number; avg_time_spent_mins: number };
  stat_significance: { p_value: number; cohens_d: number };
}

interface AgentStatus {
  status: string;
  latency_ms: number;
  errors_24h: number;
}

export default function AdminDashboard() {
  const [learners, setLearners] = useState<Learner[]>([]);
  const [cohortStats, setCohortStats] = useState<CohortStats | null>(null);
  const [health, setHealth] = useState<Record<string, AgentStatus>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Poll data every 30 seconds
    const fetchData = async () => {
      try {
        const [learnersRes, statsRes, healthRes] = await Promise.all([
          fetch('http://localhost:8000/api/v1/admin/stats/learners'),
          fetch('http://localhost:8000/api/v1/admin/stats/cohort-comparison'),
          fetch('http://localhost:8000/api/v1/admin/stats/agent-health')
        ]);

        if (learnersRes.ok) {
          const data = await learnersRes.json();
          setLearners(data.learners);
        }
        if (statsRes.ok) {
          setCohortStats(await statsRes.json());
        }
        if (healthRes.ok) {
          const data = await healthRes.json();
          setHealth(data.agents);
        }
      } catch (error) {
        console.error("Failed to fetch admin stats:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="p-10 text-center text-xl">Loading Admin Dashboard...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🎓 Admin Dashboard</h1>
          <p className="text-gray-500">Real-time Pilot Monitoring</p>
        </div>
        <div className="bg-white px-4 py-2 rounded shadow text-sm">
          Status: <span className="text-green-600 font-bold">LIVE</span>
        </div>
      </header>

      {/* 1. Cohort Comparison (Key Metric) */}
      <section className="mb-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow border border-blue-100">
          <h2 className="text-xl font-semibold mb-4 text-blue-800">🧪 Experiment Results (Live)</h2>
          {cohortStats && (
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                <span className="font-medium text-blue-900">Treatment (Full AI)</span>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-700">{(cohortStats.treatment.avg_mastery * 100).toFixed(1)}%</div>
                  <div className="text-xs text-blue-600">Avg Mastery (N={cohortStats.treatment.count})</div>
                </div>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <span className="font-medium text-gray-700">Control (Baseline)</span>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-700">{(cohortStats.control.avg_mastery * 100).toFixed(1)}%</div>
                  <div className="text-xs text-gray-500">Avg Mastery (N={cohortStats.control.count})</div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-100 flex justify-between text-sm">
                <span>Cohen's d: <strong>{cohortStats.stat_significance.cohens_d}</strong></span>
                <span>p-value: <strong>{cohortStats.stat_significance.p_value}</strong></span>
                <span className="text-green-600 font-bold">
                  {cohortStats.stat_significance.cohens_d > 0.5 ? "LARGE EFFECT" : "MODERATE"}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* 2. System Health */}
        <div className="bg-white p-6 rounded-lg shadow border border-green-100">
          <h2 className="text-xl font-semibold mb-4 text-green-800">🤖 Agent Health</h2>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(health).map(([name, status]) => (
              <div key={name} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                <span className="text-sm font-medium capitalize">{name.replace('agent_', '').replace(/_/g, ' ')}</span>
                <div className="flex items-center space-x-2">
                  <span className={`h-2 w-2 rounded-full ${status.status === 'UP' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                  <span className="text-xs text-gray-500">{status.latency_ms}ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 3. Learner Roster */}
      <section className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h2 className="text-xl font-semibold text-gray-900">📚 Learner Roster</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-600">
            <thead className="bg-gray-50 text-gray-900 uppercase font-medium">
              <tr>
                <th className="px-6 py-3">Learner</th>
                <th className="px-6 py-3">Cohort</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Progress</th>
                <th className="px-6 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {learners.map((learner) => (
                <tr key={learner.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{learner.name}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      learner.cohort === 'TREATMENT' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'
                    }`}>
                      {learner.cohort}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`flex items-center space-x-1 ${
                      learner.status === 'ACTIVE' ? 'text-green-600' : 'text-gray-400'
                    }`}>
                      <span className="h-1.5 w-1.5 rounded-full bg-current"></span>
                      <span>{learner.status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div 
                        className="bg-blue-600 h-2.5 rounded-full" 
                        style={{ width: `${learner.progress}%` }}
                      ></div>
                    </div>
                    <span className="text-xs mt-1 block">{learner.progress}%</span>
                  </td>
                  <td className="px-6 py-4">
                    <button className="text-blue-600 hover:text-blue-800 font-medium text-xs">View Detail</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
