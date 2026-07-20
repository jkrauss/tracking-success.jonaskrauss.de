import { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { api, MetricConfig, MetricHistory } from '@/lib/api';

interface MetricChartProps {
  config: MetricConfig;
  days: number;
}

export function MetricChart({ config, days }: MetricChartProps) {
  const [data, setData] = useState<MetricHistory | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [config.id, days]);

  const loadData = async () => {
    try {
      setLoading(true);
      const history = await api.metrics.getEntries(config.id, days);
      setData(history);
    } catch (error) {
      console.error('Failed to load chart data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data) {
    return <div className="h-24 flex items-center justify-center text-muted-foreground text-xs">...</div>;
  }

  const chartData = data.entries.map((entry) => {
    let value: number | null = null;
    if (config.metric_type === 'bool') {
      value = entry.success ? 1 : 0;
    } else if (entry.computed_value !== null) {
      value = entry.computed_value;
    } else if (entry.value_float !== null) {
      value = entry.value_float;
    }

    return {
      date: new Date(entry.entry_date).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' }),
      value,
    };
  });

  const formatValue = (val: number) => {
    if (config.metric_type === 'bool') return val === 1 ? '✓' : '✗';
    return val.toFixed(1);
  };

  return (
    <div className="flex-1 min-h-24">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 9, fill: 'hsl(var(--muted-foreground))' }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 9, fill: 'hsl(var(--muted-foreground))' }}
            tickLine={false}
            tickFormatter={formatValue}
            width={28}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--card))',
              border: '1px solid hsl(var(--border))',
              borderRadius: 'var(--radius)',
              fontSize: 11,
              padding: '4px 8px',
            }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="hsl(var(--primary))"
            strokeWidth={1.5}
            dot={{ fill: 'hsl(var(--primary))', r: 2 }}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
