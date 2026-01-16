'use client';

import { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Key,
  Bell,
  Shield,
  Palette,
  Server,
  Save,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  Copy,
  Check,
  Loader2,
} from 'lucide-react';
import { useStore } from '@/lib/store';
import { getSettings } from '@/lib/api';
import { createApiKey, listApiKeys, revokeApiKey, type APIKey } from '@/lib/auth';

export default function SettingsPage() {
  const { user } = useStore();
  const [activeTab, setActiveTab] = useState('general');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    llm_provider: 'ollama',
    openai_model: 'gpt-4o-mini',
    ollama_model: 'llama3.2',
    openai_configured: false,
    ollama_available: true,
    tools_count: 0,
    agents_count: 0,
  });

  // API Keys state
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await getSettings();
      setSettings(data);
      const keys = await listApiKeys();
      setApiKeys(keys);
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApiKey = async () => {
    if (!newKeyName.trim()) return;

    try {
      const key = await createApiKey(newKeyName);
      setNewKey(key.key);
      setNewKeyName('');
      const keys = await listApiKeys();
      setApiKeys(keys);
    } catch (error) {
      console.error('Failed to create API key:', error);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to revoke this API key?')) return;

    try {
      await revokeApiKey(keyId);
      setApiKeys((prev) => prev.filter((k) => k.id !== keyId));
    } catch (error) {
      console.error('Failed to revoke API key:', error);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const tabs = [
    { id: 'general', label: 'General', icon: SettingsIcon },
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'providers', label: 'LLM Providers', icon: Server },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-gray-400 mt-1">Manage your account and application settings</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-800 p-1 rounded-lg w-fit">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
        {/* General Settings */}
        {activeTab === 'general' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-white mb-4">Account Information</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Username
                  </label>
                  <input
                    type="text"
                    value={user?.username || ''}
                    disabled
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-gray-400 cursor-not-allowed"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
                  <input
                    type="email"
                    value={user?.email || ''}
                    disabled
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-gray-400 cursor-not-allowed"
                  />
                </div>
              </div>
            </div>

            <div className="border-t border-gray-700 pt-6">
              <h3 className="text-lg font-medium text-white mb-4">System Status</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400">Active Tools</div>
                  <div className="text-2xl font-bold text-white">{settings.tools_count}</div>
                </div>
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400">Active Agents</div>
                  <div className="text-2xl font-bold text-white">{settings.agents_count}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* API Keys */}
        {activeTab === 'api-keys' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-white mb-2">API Keys</h3>
              <p className="text-sm text-gray-400 mb-4">
                Create API keys to access the agent programmatically
              </p>

              {/* Create new key */}
              <div className="flex gap-2 mb-6">
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Key name (e.g., 'Production API')"
                />
                <button
                  onClick={handleCreateApiKey}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Create Key
                </button>
              </div>

              {/* New key display */}
              {newKey && (
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 mb-6">
                  <p className="text-sm text-green-400 mb-2">
                    Your new API key has been created. Copy it now - you won't be able to see it
                    again!
                  </p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 bg-gray-900 px-3 py-2 rounded text-sm text-white font-mono overflow-x-auto">
                      {newKey}
                    </code>
                    <button
                      onClick={() => copyToClipboard(newKey)}
                      className="p-2 hover:bg-gray-700 rounded text-gray-400 hover:text-white"
                    >
                      {copiedKey ? (
                        <Check className="w-5 h-5 text-green-400" />
                      ) : (
                        <Copy className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Existing keys */}
              <div className="space-y-2">
                {apiKeys.length === 0 ? (
                  <p className="text-gray-400 text-center py-8">No API keys created yet</p>
                ) : (
                  apiKeys.map((key) => (
                    <div
                      key={key.id}
                      className="flex items-center justify-between bg-gray-700/50 rounded-lg p-3"
                    >
                      <div>
                        <div className="font-medium text-white">{key.name}</div>
                        <div className="text-xs text-gray-400">
                          Created {new Date(key.created_at).toLocaleDateString()} • Last used:{' '}
                          {key.last_used
                            ? new Date(key.last_used).toLocaleDateString()
                            : 'Never'}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRevokeKey(key.id)}
                        className="p-2 hover:bg-red-500/20 rounded text-gray-400 hover:text-red-400 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* LLM Providers */}
        {activeTab === 'providers' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-white mb-4">LLM Provider Configuration</h3>

              <div className="space-y-4">
                {/* Current provider */}
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                  <div className="text-sm text-blue-400 mb-1">Current Provider</div>
                  <div className="text-lg font-medium text-white capitalize">
                    {settings.llm_provider}
                  </div>
                  <div className="text-sm text-gray-400 mt-1">
                    Model: {settings.llm_provider === 'openai' ? settings.openai_model : settings.ollama_model}
                  </div>
                </div>

                {/* Provider status */}
                <div className="grid grid-cols-2 gap-4">
                  <div
                    className={`rounded-lg p-4 ${
                      settings.openai_configured
                        ? 'bg-green-500/10 border border-green-500/30'
                        : 'bg-gray-700/50 border border-gray-600'
                    }`}
                  >
                    <div className="font-medium text-white">OpenAI</div>
                    <div
                      className={`text-sm ${
                        settings.openai_configured ? 'text-green-400' : 'text-gray-400'
                      }`}
                    >
                      {settings.openai_configured ? 'Configured' : 'Not configured'}
                    </div>
                  </div>
                  <div
                    className={`rounded-lg p-4 ${
                      settings.ollama_available
                        ? 'bg-green-500/10 border border-green-500/30'
                        : 'bg-gray-700/50 border border-gray-600'
                    }`}
                  >
                    <div className="font-medium text-white">Ollama</div>
                    <div
                      className={`text-sm ${
                        settings.ollama_available ? 'text-green-400' : 'text-gray-400'
                      }`}
                    >
                      {settings.ollama_available ? 'Available' : 'Not available'}
                    </div>
                  </div>
                </div>

                <p className="text-sm text-gray-400">
                  To change LLM providers or add API keys, update the .env file in the backend
                  directory and restart the server.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
