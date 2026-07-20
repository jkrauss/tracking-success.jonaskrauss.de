import { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { api, MetricConfig, MetricHistory } from '@/lib/api';

interface MetricChartProps {
  config: MetricConfig;
  days: number;
}

/** "Nice" step size for axis ticks (1-2-5 rule). */
function getNiceStep(range: number): number {
  if (range <= 0) return 1;
  const mag = Math.pow(10, Math.floor(Math.log10(range)));
  const r = range / mag;
  if (r <= 1.5) return mag * 0.2;
  if (r <= 4) return mag * 0.5;
  if (r <= 8) return mag;
  return mag * 2;
}

/** Heuristic Y-axis domain. Bool: [0,1.2]. Percent: [0,100]. Otherwise nice-range with 5% padding. */
function getYDomain(config: MetricConfig, values: number[]): [number, number] {
  if (config.metric_type === 'bool') return [0, 1.2];
  if (values.length === 0) return [0, 10];
  if (config.unit === '%') return [0, 100];

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min;

  if (range === 0) {
    const pad = Math.max(Math.abs(min) * 0.2, 1);
    const dec = 1;
    return [parseFloat((min - pad).toFixed(dec)), parseFloat((max + pad).toFixed(dec))];
  }

  const padding = range * 0.05;
  const step = getNiceStep(range);
  const dec = Math.max(0, -Math.floor(Math.log10(step)));
  return [
    parseFloat((Math.floor((min - padding) / step) * step).toFixed(dec)),
    parseFloat((Math.ceil((max + padding) / step) * step).toFixed(dec)),
  ];
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
            domain={getYDomain(config, chartData.map(d => d.value).filter((v): v is number => v !== null))}
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
