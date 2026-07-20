import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api, TodaySummary, MetricConfig } from '@/lib/api';
import { CheckCircle, XCircle, BarChart3 } from 'lucide-react';
import {
  LineChart, Line, Tooltip, ResponsiveContainer
} from 'recharts';

export function SummaryCard() {
  const [summary, setSummary] = useState<TodaySummary | null>(null);
  const [configs, setConfigs] = useState<MetricConfig[]>([]);
  const [historyData, setHistoryData] = useState<Array<{ date: string; success: number; fail: number }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [summaryData, configsData, historyResult] = await Promise.all([
        api.metrics.getTodaySummary(),
        api.metrics.getConfigs(),
        api.metrics.getSummaryHistory(7),
      ]);
      setSummary(summaryData);
      setConfigs(configsData);
      setHistoryData(historyResult.history);
    } catch (error) {
      console.error('Failed to load summary:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !summary) {
    return (
      <Card className="w-full">
        <CardContent className="p-3">
          <div className="animate-pulse h-16 bg-muted rounded" />
        </CardContent>
      </Card>
    );
  }

  const goalConfigs = configs.filter((c) => c.has_goal);
  const successRate = goalConfigs.length > 0
    ? Math.round((summary.success / goalConfigs.length) * 100)
    : 0;

  const chartData = historyData.map(d => ({
    date: new Date(d.date).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' }),
    success: d.success,
    fail: d.fail,
  }));

  return (
    <Card className="w-full">
      <CardHeader className="py-1.5 px-3">
        <CardTitle className="flex items-center gap-1.5 text-sm">
          <BarChart3 className="w-4 h-4" />
          Heute
        </CardTitle>
      </CardHeader>
      <CardContent className="px-3 pb-2 pt-0">
        <div className="flex items-center gap-3">
          {/* Stats — horizontal */}
          <div className="flex gap-2 shrink-0">
            <div className="flex items-center gap-1 text-green-600">
              <CheckCircle className="w-4 h-4" />
              <span className="text-sm font-bold">{summary.success}</span>
            </div>
            <div className="flex items-center gap-1 text-red-500">
              <XCircle className="w-4 h-4" />
              <span className="text-sm font-bold">{summary.fail}</span>
            </div>
            <div className="text-sm font-bold text-blue-500">
              {successRate}%
            </div>
          </div>

          {/* Chart — inline */}
          <div className="flex-1 h-10 min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: 'var(--radius)',
                    fontSize: 11,
                    padding: '2px 6px',
                  }}
                />
                <Line type="monotone" dataKey="success" stroke="#22c55e" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="fail" stroke="#ef4444" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
