import { useState, useEffect } from 'react';
import { BarChart3, Star, Clock, Hash, TrendingUp } from 'lucide-react';
import { api } from '../api';
import type { Prompt, PromptStats, VersionStats } from '../types';

interface Props {
  prompt: Prompt;
}

export default function StatsView({ prompt }: Props) {
  const [stats, setStats] = useState<PromptStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, [prompt.id]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await api.getStats(prompt.id);
      setStats(data);
    } catch (e) {
      console.error('Failed to load stats:', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-dark-400">Loading stats...</div>
      </div>
    );
  }

  if (!stats || stats.versions.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <BarChart3 className="w-12 h-12 text-dark-600 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-white mb-1">No Data Yet</h3>
          <p className="text-sm text-dark-400">Run some prompts and rate them to see improvement tracking.</p>
        </div>
      </div>
    );
  }

  const maxRating = Math.max(...stats.versions.map((v) => v.avg_rating), 1);
  const maxLatency = Math.max(...stats.versions.map((v) => v.avg_latency_ms), 1);

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-dark-900 border-b border-dark-700 px-6 py-4">
        <h2 className="text-xl font-bold text-white">Track Improvements</h2>
        <p className="text-sm text-dark-400 mt-0.5">
          Monitor quality, latency, and usage across prompt versions
        </p>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-4">
          <SummaryCard
            icon={<Hash className="w-5 h-5 text-indigo-400" />}
            label="Total Versions"
            value={stats.versions.length.toString()}
          />
          <SummaryCard
            icon={<BarChart3 className="w-5 h-5 text-emerald-400" />}
            label="Total Runs"
            value={stats.versions.reduce((a, v) => a + v.total_runs, 0).toString()}
          />
          <SummaryCard
            icon={<Star className="w-5 h-5 text-yellow-400" />}
            label="Best Rating"
            value={Math.max(...stats.versions.map((v) => v.avg_rating)).toFixed(1)}
          />
          <SummaryCard
            icon={<TrendingUp className="w-5 h-5 text-purple-400" />}
            label="Fastest Response"
            value={`${Math.min(...stats.versions.filter((v) => v.avg_latency_ms > 0).map((v) => v.avg_latency_ms)).toFixed(0)}ms`}
          />
        </div>

        {/* Version Comparison Table */}
        <div className="bg-dark-900 border border-dark-700 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-dark-700">
            <h3 className="text-sm font-semibold text-white">Version Performance</h3>
          </div>
          <table className="w-full">
            <thead>
              <tr className="text-xs text-dark-400 uppercase tracking-wider">
                <th className="text-left px-5 py-3">Version</th>
                <th className="text-center px-5 py-3">Runs</th>
                <th className="text-center px-5 py-3">Avg Rating</th>
                <th className="text-center px-5 py-3">Avg Latency</th>
                <th className="text-center px-5 py-3">Avg Tokens</th>
                <th className="text-right px-5 py-3">Quality</th>
              </tr>
            </thead>
            <tbody>
              {stats.versions.map((v) => (
                <tr key={v.version_id} className="border-t border-dark-800 hover:bg-dark-800/50">
                  <td className="px-5 py-3">
                    <span className="text-sm font-medium text-indigo-400">v{v.version_number}</span>
                  </td>
                  <td className="text-center px-5 py-3 text-sm text-dark-300">{v.total_runs}</td>
                  <td className="text-center px-5 py-3">
                    <div className="flex items-center justify-center gap-1">
                      <Star className={`w-3.5 h-3.5 ${v.avg_rating > 0 ? 'text-yellow-400 fill-yellow-400' : 'text-dark-600'}`} />
                      <span className="text-sm text-dark-300">{v.avg_rating > 0 ? v.avg_rating.toFixed(1) : '-'}</span>
                    </div>
                  </td>
                  <td className="text-center px-5 py-3">
                    <span className="text-sm text-dark-300">
                      {v.avg_latency_ms > 0 ? `${v.avg_latency_ms.toFixed(0)}ms` : '-'}
                    </span>
                  </td>
                  <td className="text-center px-5 py-3">
                    <span className="text-sm text-dark-300">
                      {v.avg_tokens > 0 ? v.avg_tokens.toFixed(0) : '-'}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex justify-end">
                      <div className="w-24 h-2 bg-dark-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all"
                          style={{ width: `${maxRating > 0 ? (v.avg_rating / 5) * 100 : 0}%` }}
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Visual Bar Charts */}
        <div className="grid grid-cols-2 gap-6">
          {/* Rating Chart */}
          <div className="bg-dark-900 border border-dark-700 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Rating by Version</h3>
            <div className="space-y-3">
              {stats.versions.map((v) => (
                <div key={v.version_id} className="flex items-center gap-3">
                  <span className="w-8 text-xs text-dark-400 text-right">v{v.version_number}</span>
                  <div className="flex-1 h-6 bg-dark-800 rounded-md overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-yellow-500 to-amber-400 rounded-md flex items-center px-2 transition-all"
                      style={{ width: `${(v.avg_rating / 5) * 100}%` }}
                    >
                      {v.avg_rating > 0 && (
                        <span className="text-xs font-medium text-dark-900">{v.avg_rating.toFixed(1)}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Latency Chart */}
          <div className="bg-dark-900 border border-dark-700 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Latency by Version</h3>
            <div className="space-y-3">
              {stats.versions.map((v) => (
                <div key={v.version_id} className="flex items-center gap-3">
                  <span className="w-8 text-xs text-dark-400 text-right">v{v.version_number}</span>
                  <div className="flex-1 h-6 bg-dark-800 rounded-md overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-blue-400 rounded-md flex items-center px-2 transition-all"
                      style={{ width: `${maxLatency > 0 ? (v.avg_latency_ms / maxLatency) * 100 : 0}%` }}
                    >
                      {v.avg_latency_ms > 0 && (
                        <span className="text-xs font-medium text-white">{v.avg_latency_ms.toFixed(0)}ms</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="bg-dark-900 border border-dark-700 rounded-xl p-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-dark-800 flex items-center justify-center">
          {icon}
        </div>
        <div>
          <div className="text-lg font-bold text-white">{value}</div>
          <div className="text-xs text-dark-400">{label}</div>
        </div>
      </div>
    </div>
  );
}
