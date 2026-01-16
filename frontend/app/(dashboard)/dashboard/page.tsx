'use client';

import { useState, useEffect } from 'react';
import {
  Activity,
  Cpu,
  DollarSign,
  MessageSquare,
  TrendingUp,
  Zap,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { getMemoryStats, checkHealth } from '@/lib/api';

// Mock data for charts - in production, this would come from the API
const usageData = [
  { date: 'Mon', requests: 45, tokens: 12500 },
  { date: 'Tue', requests: 52, tokens: 15800 },
  { date: 'Wed', requests: 38, tokens: 9200 },
  { date: 'Thu', requests: 65, tokens: 21000 },
  { date: 'Fri', requests: 48, tokens: 14200 },
  { date: 'Sat', requests: 25, tokens: 7500 },
  { date: 'Sun', requests: 30, tokens: 8900 },
];

const providerData = [
  { name: 'OpenAI', value: 45, color: '#10b981' },
  { name: 'Anthropic', value: 30, color: '#8b5cf6' },
  { name: 'Gemini', value: 15, color: '#3b82f6' },
  { name: 'Ollama', value: 10, color: '#f59e0b' },
];

const costData = [
  { date: 'Mon', cost: 0.45 },
  { date: 'Tue', cost: 0.52 },
  { date: 'Wed', cost: 0.38 },
  { date: 'Thu', cost: 0.65 },
  { date: 'Fri', cost: 0.48 },
  { date: 'Sat', cost: 0.15 },
  { date: 'Sun', cost: 0.20 },
];

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: any;
  iconColor: string;
}

function StatCard({ title, value, change, changeType = 'neutral', icon: Icon, iconColor }: StatCardProps) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {change && (
            <p
              className={`text-xs mt-1 flex items-center gap-1 ${
                changeType === 'positive'
                  ? 'text-green-400'
                  : changeType === 'negative'
                  ? 'text-red-400'
                  : 'text-gray-400'
              }`}
            >
              {changeType === 'positive' && <TrendingUp className="w-3 h-3" />}
              {change}
            </p>
          )}
        </div>
        <div className={`p-2 ${iconColor} rounded-lg`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalRequests: 303,
    totalTokens: 89100,
    totalCost: 2.83,
    avgResponseTime: 1.2,
  });
  const [systemHealth, setSystemHealth] = useState({
    healthy: true,
    llmProvider: 'ollama',
    toolsCount: 10,
    agentsCount: 4,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const health = await checkHealth();
      setSystemHealth({
        healthy: health,
        llmProvider: 'ollama',
        toolsCount: 10,
        agentsCount: 4,
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Monitor your AI agent's performance and usage</p>
      </div>

      {/* System Status */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`p-2 rounded-full ${
                systemHealth.healthy ? 'bg-green-500/20' : 'bg-red-500/20'
              }`}
            >
              {systemHealth.healthy ? (
                <CheckCircle className="w-5 h-5 text-green-400" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-400" />
              )}
            </div>
            <div>
              <p className="font-medium text-white">
                System {systemHealth.healthy ? 'Healthy' : 'Degraded'}
              </p>
              <p className="text-sm text-gray-400">
                {systemHealth.toolsCount} tools, {systemHealth.agentsCount} agents active
              </p>
            </div>
          </div>
          <div className="text-sm text-gray-400">
            Provider: <span className="text-white capitalize">{systemHealth.llmProvider}</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Requests"
          value={stats.totalRequests.toLocaleString()}
          change="+12% from last week"
          changeType="positive"
          icon={MessageSquare}
          iconColor="bg-blue-600"
        />
        <StatCard
          title="Total Tokens"
          value={`${(stats.totalTokens / 1000).toFixed(1)}K`}
          change="+8% from last week"
          changeType="positive"
          icon={Zap}
          iconColor="bg-purple-600"
        />
        <StatCard
          title="Total Cost"
          value={`$${stats.totalCost.toFixed(2)}`}
          change="-5% from last week"
          changeType="positive"
          icon={DollarSign}
          iconColor="bg-green-600"
        />
        <StatCard
          title="Avg Response Time"
          value={`${stats.avgResponseTime}s`}
          change="Same as last week"
          changeType="neutral"
          icon={Clock}
          iconColor="bg-amber-600"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Usage Over Time */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
          <h3 className="font-medium text-white mb-4">Usage Over Time</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={usageData}>
                <defs>
                  <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="requests"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorRequests)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Provider Distribution */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
          <h3 className="font-medium text-white mb-4">Provider Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={providerData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {providerData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Legend
                  verticalAlign="middle"
                  align="right"
                  layout="vertical"
                  wrapperStyle={{ fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cost Trend */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
          <h3 className="font-medium text-white mb-4">Cost Trend</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={costData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} tickFormatter={(v) => `$${v}`} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                  formatter={(value: number) => [`$${value.toFixed(2)}`, 'Cost']}
                />
                <Bar dataKey="cost" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Token Usage */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
          <h3 className="font-medium text-white mb-4">Token Usage</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={usageData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} tickFormatter={(v) => `${v / 1000}K`} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                  formatter={(value: number) => [`${value.toLocaleString()} tokens`, 'Tokens']}
                />
                <Line
                  type="monotone"
                  dataKey="tokens"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  dot={{ fill: '#8b5cf6', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
