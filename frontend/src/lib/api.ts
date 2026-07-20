const API_BASE = '/api';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}

export interface User {
  id: number;
  email: string;
}

export interface MetricConfig {
  id: number;
  name: string;
  slug: string;
  metric_type: string;
  unit: string | null;
  has_goal: boolean;
  goal_type: string | null;
  goal_value: number | null;
  calculation: string | null;
  input_fields: string | null;
  order: number;
}

export interface MetricEntry {
  id: number;
  config_id: number;
  entry_date: string;
  value_bool: boolean | null;
  value_float: number | null;
  value_time_1: string | null;
  value_time_2: string | null;
  computed_value: number | null;
  success: boolean | null;
}

export interface MetricHistory {
  entries: MetricEntry[];
  current_streak: number;
}

export interface TodaySummary {
  date: string;
  success: number;
  fail: number;
  total: number;
  entries: Array<{ config_id: number; success: boolean | null; computed_value: number | null }>;
}

export const api = {
  auth: {
    register: (email: string, password: string) =>
      request<User>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    login: (email: string, password: string) =>
      request<{ access_token: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
  },
  metrics: {
    getConfigs: () => request<MetricConfig[]>('/metrics/configs'),
    createConfig: (data: Partial<MetricConfig>) =>
      request<MetricConfig>('/metrics/configs', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    updateConfig: (id: number, data: Partial<MetricConfig>) =>
      request<MetricConfig>(`/metrics/configs/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    deleteConfig: (id: number) =>
      request<{ ok: boolean }>(`/metrics/configs/${id}`, {
        method: 'DELETE',
      }),
    createEntry: (configId: number, data: Partial<MetricEntry>) =>
      request<MetricEntry>(`/metrics/entries?config_id=${configId}`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    getEntries: (configId: number, days: number = 7) =>
      request<MetricHistory>(`/metrics/entries/${configId}?days=${days}`),
    getTodaySummary: () => request<TodaySummary>('/metrics/summary/today'),
    getSummaryHistory: (days: number = 7) =>
      request<{ days: number; total_configs: number; history: Array<{ date: string; success: number; fail: number; total_configs: number }> }>(`/metrics/summary/history?days=${days}`),
  },
  yaml: {
    export: () => request<{ yaml: string }>('/yaml/export'),
    import: (yaml: string) =>
      request<{ ok: boolean; count: number }>('/yaml/import', {
        method: 'POST',
        body: JSON.stringify(yaml),
        headers: { 'Content-Type': 'application/json' },
      }),
    initDefaults: () =>
      request<{ ok: boolean; count: number }>('/yaml/init-defaults', {
        method: 'POST',
      }),
  },
};
