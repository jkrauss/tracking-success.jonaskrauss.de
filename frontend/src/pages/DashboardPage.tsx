import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/hooks/useAuth';
import { api, MetricConfig } from '@/lib/api';
import { MetricCard } from '@/components/cards/MetricCard';
import { SummaryCard } from '@/components/cards/SummaryCard';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ChevronLeft, ChevronRight, Settings, LogOut, Plus, Check } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [configs, setConfigs] = useState<MetricConfig[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showSummary, setShowSummary] = useState(true);
  const [doneConfigs, setDoneConfigs] = useState<Set<number>>(new Set());

  // Swipe detection on the card area
  const cardAreaRef = useRef<HTMLDivElement>(null);
  const touchStartX = useRef(0);
  const touchStartY = useRef(0);
  const touchStartTime = useRef(0);
  const isSwiping = useRef(false);

  useEffect(() => {
    loadConfigs();
    loadTodayDone();
  }, []);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const data = await api.metrics.getConfigs();
      setConfigs(data);
      if (data.length === 0) {
        await api.yaml.initDefaults();
        const newData = await api.metrics.getConfigs();
        setConfigs(newData);
      }
    } catch (error) {
      console.error('Failed to load configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTodayDone = async () => {
    try {
      const summary = await api.metrics.getTodaySummary();
      const done = new Set<number>();
      for (const e of summary.entries) {
        // Card is "done" if it has any entry today (success can be null for no-goal cards)
        done.add(e.config_id);
      }
      setDoneConfigs(done);
    } catch (error) {
      console.error('Failed to load today summary:', error);
    }
  };

  const handlePrev = useCallback(() => {
    setCurrentIndex((prev) => (prev - 1 + configs.length) % configs.length);
  }, [configs.length]);

  const handleNext = useCallback(() => {
    setCurrentIndex((prev) => (prev + 1) % configs.length);
  }, [configs.length]);

  // Swipe handlers — on the card area, but ignore if touch started on input/button
  const onTouchStart = (e: React.TouchEvent) => {
    const target = e.target as HTMLElement;
    // Don't swipe if touching an input, button, or their children
    if (target.closest('input, button, [role="button"], select, textarea')) {
      isSwiping.current = false;
      return;
    }
    touchStartX.current = e.touches[0].clientX;
    touchStartY.current = e.touches[0].clientY;
    touchStartTime.current = Date.now();
    isSwiping.current = true;
  };

  const onTouchEnd = (e: React.TouchEvent) => {
    if (!isSwiping.current) return;
    isSwiping.current = false;

    const dx = e.changedTouches[0].clientX - touchStartX.current;
    const dy = e.changedTouches[0].clientY - touchStartY.current;
    const dt = Date.now() - touchStartTime.current;

    // Horizontal swipe: min 50px, max 500ms, must be more horizontal than vertical
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5 && dt < 500) {
      if (dx < 0) handleNext();
      else handlePrev();
    }
  };

  const handleCardSaved = () => {
    loadTodayDone();
    setShowSummary(false);
    setTimeout(() => setShowSummary(true), 100);
  };

  if (loading) {
    return (
      <div className="h-[100dvh] flex items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="h-[100dvh] flex flex-col bg-background overflow-hidden">
      {/* Header — compact */}
      <header className="shrink-0 border-b bg-card px-3 py-2 flex items-center justify-between">
        <h1 className="text-base font-bold">📊 Tracking</h1>
        <div className="flex items-center gap-1">
          <span className="text-xs text-muted-foreground hidden sm:inline mr-1">
            {user?.email}
          </span>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => navigate('/settings')}>
            <Settings className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={logout}>
            <LogOut className="w-4 h-4" />
          </Button>
        </div>
      </header>

      {/* Content — fills remaining space */}
      <main className="flex-1 flex flex-col min-h-0 px-3 py-2 gap-2">
        {/* Summary — compact, fixed height */}
        {showSummary && (
          <div className="shrink-0">
            <SummaryCard />
          </div>
        )}

        {/* Metric card area — takes remaining space, swipeable */}
        {configs.length > 0 ? (
          <div className="flex-1 flex flex-col min-h-0">
            {/* Card — fills available space, swipeable */}
            <div
              ref={cardAreaRef}
              onTouchStart={onTouchStart}
              onTouchEnd={onTouchEnd}
              className="flex-1 min-h-0 overflow-y-auto touch-pan-y"
            >
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentIndex}
                  initial={{ opacity: 0, x: 30 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -30 }}
                  transition={{ duration: 0.15 }}
                  className="h-full"
                >
                  <MetricCard
                    config={configs[currentIndex]}
                    onSuccess={handleCardSaved}
                  />
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Navigation — below card, always visible */}
            <div className="shrink-0 flex items-center justify-between pt-2 pb-1">
              <Button variant="outline" size="icon" className="h-8 w-8" onClick={handlePrev}>
                <ChevronLeft className="w-4 h-4" />
              </Button>

              <div className="flex items-center gap-1.5">
                {configs.map((config, index) => {
                  const isDone = doneConfigs.has(config.id);
                  const isCurrent = index === currentIndex;
                  return (
                    <button
                      key={config.id}
                      onClick={() => setCurrentIndex(index)}
                      className={`relative w-4 h-4 rounded-full transition-all flex items-center justify-center ${
                        isCurrent
                          ? 'bg-primary scale-110'
                          : isDone
                            ? 'bg-green-500'
                            : 'bg-muted-foreground/30'
                      }`}
                      title={config.name}
                    >
                      {isDone && (
                        <Check className="w-2.5 h-2.5 text-white" strokeWidth={3} />
                      )}
                    </button>
                  );
                })}
                <span className="text-xs text-muted-foreground ml-1">
                  {currentIndex + 1}/{configs.length}
                </span>
              </div>

              <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleNext}>
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        ) : (
          <Card className="p-6 text-center">
            <p className="text-muted-foreground mb-3 text-sm">
              Noch keine Kennzahlen konfiguriert.
            </p>
            <Button size="sm" onClick={() => navigate('/settings')}>
              <Plus className="w-4 h-4 mr-1" />
              Einrichten
            </Button>
          </Card>
        )}
      </main>
    </div>
  );
}
