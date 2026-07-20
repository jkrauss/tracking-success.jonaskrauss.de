import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MetricChart } from '@/components/charts/MetricChart';
import { api, MetricConfig, MetricEntry } from '@/lib/api';
import { CheckCircle, XCircle, Flame } from 'lucide-react';

interface MetricCardProps {
  config: MetricConfig;
  onSuccess?: () => void;
}

const STREAK_MILESTONES = [3, 7, 14, 30, 60, 90, 183, 365];

export function MetricCard({ config, onSuccess }: MetricCardProps) {
  const [entry, setEntry] = useState<MetricEntry | null>(null);
  const [streak, setStreak] = useState(0);
  const [chartDays, setChartDays] = useState(7);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [showFailure, setShowFailure] = useState(false);
  const [showStreak, setShowStreak] = useState(false);
  const [streakMilestone, setStreakMilestone] = useState(0);

  const [boolValue, setBoolValue] = useState(false);
  const [floatValue, setFloatValue] = useState('');
  const [time1, setTime1] = useState('');
  const [time2, setTime2] = useState('');

  useEffect(() => {
    loadTodayEntry();
  }, [config.id]);

  const loadTodayEntry = async () => {
    try {
      setLoading(true);
      const history = await api.metrics.getEntries(config.id, 1);
      if (history.entries.length > 0) {
        const today = history.entries[history.entries.length - 1];
        setEntry(today);
        setBoolValue(today.value_bool || false);
        setFloatValue(today.value_float?.toString() || '');
        setTime1(today.value_time_1 || '');
        setTime2(today.value_time_2 || '');
      }
      setStreak(history.current_streak);
    } catch (error) {
      console.error('Failed to load entry:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      const data: any = {
        entry_date: new Date().toISOString().split('T')[0],
      };

      if (config.metric_type === 'bool') {
        data.value_bool = boolValue;
      } else if (config.metric_type === 'float' || config.metric_type === 'weight') {
        data.value_float = parseFloat(floatValue) || 0;
      } else if (config.metric_type === 'sleep' || config.metric_type === 'fasting') {
        data.value_time_1 = time1 || null;
        data.value_time_2 = time2 || null;
      }

      const result = await api.metrics.createEntry(config.id, data);
      setEntry(result);
      onSuccess?.();

      if (result.success === true) {
        setShowSuccess(true);
        setTimeout(() => setShowSuccess(false), 2000);

        const newHistory = await api.metrics.getEntries(config.id, 365);
        const newStreak = newHistory.current_streak;
        setStreak(newStreak);

        if (STREAK_MILESTONES.includes(newStreak) && newStreak > streak) {
          setStreakMilestone(newStreak);
          setShowStreak(true);
          setTimeout(() => setShowStreak(false), 3000);
        }
      } else if (result.success === false) {
        setShowFailure(true);
        setTimeout(() => setShowFailure(false), 2000);
      }
    } catch (error) {
      console.error('Failed to save entry:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const renderInput = () => {
    if (config.metric_type === 'bool') {
      return (
        <Button
          variant={boolValue ? 'default' : 'outline'}
          className="w-full h-10 text-sm"
          onClick={() => setBoolValue(!boolValue)}
        >
          {boolValue ? '✓ Erledigt' : '✗ Nicht erledigt'}
        </Button>
      );
    }

    if (config.metric_type === 'float' || config.metric_type === 'weight') {
      return (
        <Input
          type="number"
          step="0.1"
          inputMode="decimal"
          placeholder={config.unit || 'Wert'}
          value={floatValue}
          onChange={(e) => setFloatValue(e.target.value)}
          className="h-10 text-sm"
        />
      );
    }

    if (config.metric_type === 'sleep' || config.metric_type === 'fasting') {
      const isSleep = config.metric_type === 'sleep';
      return (
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-muted-foreground mb-0.5 block">{isSleep ? 'Bettzeit' : 'Abendessen'}</label>
            <Input
              type="time"
              value={isSleep ? time1 : time2}
              onChange={(e) => isSleep ? setTime1(e.target.value) : setTime2(e.target.value)}
              className="h-10 text-sm"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-0.5 block">{isSleep ? 'Aufstehzeit' : 'Frühstück'}</label>
            <Input
              type="time"
              value={isSleep ? time2 : time1}
              onChange={(e) => isSleep ? setTime2(e.target.value) : setTime1(e.target.value)}
              className="h-10 text-sm"
            />
          </div>
        </div>
      );
    }

    return null;
  };

  const getSuccessIcon = () => {
    if (entry?.success === true) return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (entry?.success === false) return <XCircle className="w-5 h-5 text-red-500" />;
    return null;
  };

  if (loading) {
    return (
      <Card className="w-full h-full">
        <CardContent className="p-4 h-full">
          <div className="animate-pulse bg-muted rounded h-full" />
        </CardContent>
      </Card>
    );
  }

  const isDone = entry !== null;
  const isSuccess = entry?.success === true;
  const isFailure = entry?.success === false;

  return (
    <Card className={`w-full h-full flex flex-col relative overflow-hidden ${
      isSuccess ? 'border-green-500/50' : 
      isFailure ? 'border-red-500/50' : 
      isDone ? 'border-blue-500/50' : ''
    }`}>
      {/* Overlays */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            className="absolute inset-0 bg-green-500/10 flex items-center justify-center z-10"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 10 }}
            >
              <CheckCircle className="w-20 h-20 text-green-500" />
            </motion.div>
          </motion.div>
        )}
        {showFailure && (
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            className="absolute inset-0 bg-red-500/10 flex items-center justify-center z-10"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 10 }}
            >
              <XCircle className="w-20 h-20 text-red-500" />
            </motion.div>
          </motion.div>
        )}
        {showStreak && (
          <motion.div
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -30 }}
            className="absolute inset-0 bg-orange-500/10 flex items-center justify-center z-10"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 10 }}
              className="text-center"
            >
              <Flame className="w-14 h-14 text-orange-500 mx-auto mb-1" />
              <p className="text-xl font-bold text-orange-500">
                🔥 {streakMilestone} Tage!
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <CardHeader className="py-2 px-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{config.name}</CardTitle>
          <div className="flex items-center gap-2">
            {getSuccessIcon()}
            {streak > 0 && (
              <div className="flex items-center gap-0.5 text-orange-500">
                <Flame className="w-3.5 h-3.5" />
                <span className="text-xs font-medium">{streak}</span>
              </div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="px-4 pb-3 pt-0 flex-1 flex flex-col min-h-0 space-y-2">
        {/* Input */}
        {renderInput()}

        {/* Save + time range buttons — single row */}
        <div className="shrink-0 flex items-center gap-2">
          <Button
            onClick={handleSubmit}
            disabled={submitting}
            size="sm"
            className="flex-1 h-9"
          >
            {submitting ? '...' : 'Speichern'}
          </Button>
          <div className="flex gap-0.5">
            {[7, 30, 365].map((days) => (
              <Button
                key={days}
                variant={chartDays === days ? 'default' : 'outline'}
                size="sm"
                className="h-9 px-2 text-xs"
                onClick={() => setChartDays(days)}
              >
                {days === 365 ? 'Alle' : `${days}d`}
              </Button>
            ))}
          </div>
        </div>

        {/* Chart — compact */}
        <MetricChart config={config} days={chartDays} />
      </CardContent>
    </Card>
  );
}
