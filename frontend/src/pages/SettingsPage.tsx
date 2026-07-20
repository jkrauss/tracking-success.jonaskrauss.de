import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api, MetricConfig } from '@/lib/api';
import { Settings, Save, FileDown, Plus, Trash2, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function SettingsPage() {
  const navigate = useNavigate();
  const [configs, setConfigs] = useState<MetricConfig[]>([]);
  const [yamlContent, setYamlContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'visual' | 'yaml'>('visual');

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const data = await api.metrics.getConfigs();
      setConfigs(data);
      const yamlData = await api.yaml.export();
      setYamlContent(yamlData.yaml);
    } catch (error) {
      console.error('Failed to load configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveYaml = async () => {
    try {
      setSaving(true);
      await api.yaml.import(yamlContent);
      await loadConfigs();
    } catch (error) {
      console.error('Failed to save YAML:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateConfig = async (id: number, data: Partial<MetricConfig>) => {
    try {
      await api.metrics.updateConfig(id, data);
      // Update local state instead of reloading to preserve focus
      setConfigs(prev => prev.map(c => c.id === id ? { ...c, ...data } : c));
    } catch (error) {
      console.error('Failed to update config:', error);
    }
  };

  const handleDeleteConfig = async (id: number) => {
    if (!confirm('Kennzahl wirklich löschen?')) return;
    try {
      await api.metrics.deleteConfig(id);
      await loadConfigs();
    } catch (error) {
      console.error('Failed to delete config:', error);
    }
  };

  const handleAddConfig = async () => {
    try {
      await api.metrics.createConfig({
        name: 'Neue Kennzahl',
        slug: `new-metric-${Date.now()}`,
        metric_type: 'bool',
        has_goal: true,
        goal_type: 'bool',
        order: configs.length,
      });
      await loadConfigs();
    } catch (error) {
      console.error('Failed to add config:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/')}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Settings className="w-8 h-8" />
            Einstellungen
          </h1>
        </div>
        <div className="flex gap-2">
          <Button
            variant={activeTab === 'visual' ? 'default' : 'outline'}
            onClick={() => setActiveTab('visual')}
          >
            Visuell
          </Button>
          <Button
            variant={activeTab === 'yaml' ? 'default' : 'outline'}
            onClick={() => setActiveTab('yaml')}
          >
            YAML
          </Button>
        </div>
      </div>

      {activeTab === 'visual' ? (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button onClick={handleAddConfig}>
              <Plus className="w-4 h-4 mr-2" />
              Neue Kennzahl
            </Button>
          </div>

          {configs.map((config) => (
            <Card key={config.id}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1 grid grid-cols-4 gap-4">
                    <Input
                      value={config.name}
                      onChange={(e) =>
                        handleUpdateConfig(config.id, { ...config, name: e.target.value })
                      }
                      placeholder="Name"
                    />
                    <select
                      value={config.metric_type}
                      onChange={(e) =>
                        handleUpdateConfig(config.id, { ...config, metric_type: e.target.value })
                      }
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    >
                      <option value="bool">Ja/Nein</option>
                      <option value="float">Zahl</option>
                      <option value="sleep">Schlaf</option>
                      <option value="weight">Gewicht</option>
                      <option value="fasting">Fasten</option>
                    </select>
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.has_goal}
                        onChange={(e) =>
                          handleUpdateConfig(config.id, { ...config, has_goal: e.target.checked })
                        }
                        className="h-4 w-4"
                      />
                      <span className="text-sm">Ziel</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteConfig(config.id)}
                      >
                        <Trash2 className="w-4 h-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>YAML-Konfiguration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <textarea
              value={yamlContent}
              onChange={(e) => setYamlContent(e.target.value)}
              className="w-full h-96 p-4 font-mono text-sm border rounded-md bg-background"
              spellCheck={false}
            />
            <div className="flex gap-2">
              <Button onClick={handleSaveYaml} disabled={saving}>
                <Save className="w-4 h-4 mr-2" />
                {saving ? 'Speichern...' : 'Speichern'}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  const blob = new Blob([yamlContent], { type: 'text/yaml' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'metrics.yaml';
                  a.click();
                }}
              >
                <FileDown className="w-4 h-4 mr-2" />
                Exportieren
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
