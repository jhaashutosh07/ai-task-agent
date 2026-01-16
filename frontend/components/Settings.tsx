'use client';

import { useState, useEffect } from 'react';
import { X, Check, AlertCircle } from 'lucide-react';
import { useStore } from '@/lib/store';
import { getSettings, updateSettings } from '@/lib/api';

export default function Settings() {
  const { showSettings, toggleSettings, settings, setSettings } = useStore();
  const [localSettings, setLocalSettings] = useState({
    llm_provider: 'openai' as 'openai' | 'ollama',
    openai_api_key: '',
    openai_model: 'gpt-4o-mini',
    ollama_model: 'llama3.2',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (showSettings) {
      loadSettings();
    }
  }, [showSettings]);

  const loadSettings = async () => {
    try {
      const data = await getSettings();
      setSettings(data);
      setLocalSettings({
        llm_provider: data.llm_provider,
        openai_api_key: '',
        openai_model: data.openai_model,
        ollama_model: data.ollama_model,
      });
    } catch (err) {
      setError('Failed to load settings');
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      await updateSettings({
        llm_provider: localSettings.llm_provider,
        ...(localSettings.openai_api_key && { openai_api_key: localSettings.openai_api_key }),
        openai_model: localSettings.openai_model,
        ollama_model: localSettings.ollama_model,
      });
      await loadSettings();
      toggleSettings();
    } catch (err) {
      setError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (!showSettings) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Settings</h2>
          <button
            onClick={toggleSettings}
            className="p-1 hover:bg-gray-700 rounded"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg flex items-center gap-2 text-red-400">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* LLM Provider */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            LLM Provider
          </label>
          <div className="flex gap-2">
            <button
              onClick={() =>
                setLocalSettings({ ...localSettings, llm_provider: 'openai' })
              }
              className={`flex-1 py-2 px-4 rounded-lg border ${
                localSettings.llm_provider === 'openai'
                  ? 'border-primary-500 bg-primary-500/20 text-primary-400'
                  : 'border-gray-600 text-gray-400 hover:border-gray-500'
              }`}
            >
              OpenAI
            </button>
            <button
              onClick={() =>
                setLocalSettings({ ...localSettings, llm_provider: 'ollama' })
              }
              className={`flex-1 py-2 px-4 rounded-lg border ${
                localSettings.llm_provider === 'ollama'
                  ? 'border-primary-500 bg-primary-500/20 text-primary-400'
                  : 'border-gray-600 text-gray-400 hover:border-gray-500'
              }`}
            >
              Ollama
            </button>
          </div>
        </div>

        {/* OpenAI Settings */}
        {localSettings.llm_provider === 'openai' && (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                OpenAI API Key
              </label>
              <input
                type="password"
                value={localSettings.openai_api_key}
                onChange={(e) =>
                  setLocalSettings({
                    ...localSettings,
                    openai_api_key: e.target.value,
                  })
                }
                placeholder={settings?.openai_configured ? '••••••••' : 'sk-...'}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
              />
              {settings?.openai_configured && (
                <p className="mt-1 text-xs text-green-400 flex items-center gap-1">
                  <Check className="w-3 h-3" /> API key is configured
                </p>
              )}
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Model
              </label>
              <select
                value={localSettings.openai_model}
                onChange={(e) =>
                  setLocalSettings({
                    ...localSettings,
                    openai_model: e.target.value,
                  })
                }
                className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-primary-500"
              >
                <option value="gpt-4o-mini">GPT-4o Mini (Recommended)</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              </select>
            </div>
          </>
        )}

        {/* Ollama Settings */}
        {localSettings.llm_provider === 'ollama' && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Model
            </label>
            <input
              type="text"
              value={localSettings.ollama_model}
              onChange={(e) =>
                setLocalSettings({
                  ...localSettings,
                  ollama_model: e.target.value,
                })
              }
              placeholder="llama3.2"
              className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
            />
            {settings?.ollama_available ? (
              <p className="mt-1 text-xs text-green-400 flex items-center gap-1">
                <Check className="w-3 h-3" /> Ollama is running
              </p>
            ) : (
              <p className="mt-1 text-xs text-yellow-400 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" /> Ollama not detected
              </p>
            )}
          </div>
        )}

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full py-2 px-4 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
}
