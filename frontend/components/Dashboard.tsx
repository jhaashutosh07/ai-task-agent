'use client';

import { useState, useEffect } from 'react';
import {
  Activity, Brain, Workflow, Clock, Database,
  Cpu, HardDrive, Zap, TrendingUp
} from 'lucide-react';
import { getInfo, getMemoryStats, listScheduledTasks, listWorkflows } from '@/lib/api';

interface DashboardStats {
  tools: string[];
  agents: string[];
  workflows: number;
  scheduledTasks: number;
  memoryItems: number;
  knowledgeEntries: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    try {
      const [info, memory, tasks, workflows] = await Promise.all([
        getInfo(),
        getMemoryStats(),
        listScheduledTasks(),
        listWorkflows()
      ]);

      setStats({
        tools: info.tools || [],
        agents: info.agents || [],
        workflows: workflows.workflows?.length || 0,
        scheduledTasks: tasks.tasks?.length || 0,
        memoryItems: memory.vector_memory?.total_memories || 0,
        knowledgeEntries: memory.knowledge_base?.total_entries || 0
      });
    } catch (err) {
      console.error('Failed to load stats:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Tools Available',
      value: stats?.tools.length || 0,
      icon: <Zap className="w-5 h-5" />,
      color: 'bg-blue-500/20 text-blue-400'
    },
    {
      title: 'Active Agents',
      value: stats?.agents.length || 0,
      icon: <Brain className="w-5 h-5" />,
      color: 'bg-purple-500/20 text-purple-400'
    },
    {
      title: 'Workflows',
      value: stats?.workflows || 0,
      icon: <Workflow className="w-5 h-5" />,
      color: 'bg-green-500/20 text-green-400'
    },
    {
      title: 'Scheduled Tasks',
      value: stats?.scheduledTasks || 0,
      icon: <Clock className="w-5 h-5" />,
      color: 'bg-orange-500/20 text-orange-400'
    },
    {
      title: 'Memory Items',
      value: stats?.memoryItems || 0,
      icon: <Database className="w-5 h-5" />,
      color: 'bg-cyan-500/20 text-cyan-400'
    },
    {
      title: 'Knowledge Entries',
      value: stats?.knowledgeEntries || 0,
      icon: <HardDrive className="w-5 h-5" />,
      color: 'bg-pink-500/20 text-pink-400'
    }
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
        <button
          onClick={loadStats}
          className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg text-gray-300"
        >
          Refresh
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((card) => (
          <div
            key={card.title}
            className="bg-gray-800 rounded-xl p-4 border border-gray-700"
          >
            <div className={`inline-flex p-2 rounded-lg ${card.color} mb-3`}>
              {card.icon}
            </div>
            <div className="text-2xl font-bold text-white">{card.value}</div>
            <div className="text-sm text-gray-400">{card.title}</div>
          </div>
        ))}
      </div>

      {/* Tools Section */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-blue-400" />
          Available Tools
        </h3>
        <div className="flex flex-wrap gap-2">
          {stats?.tools.map((tool) => (
            <span
              key={tool}
              className="px-3 py-1 bg-gray-700 rounded-full text-sm text-gray-300"
            >
              {tool}
            </span>
          ))}
        </div>
      </div>

      {/* Agents Section */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-400" />
          AI Agents
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {stats?.agents.map((agent) => (
            <div
              key={agent}
              className="p-4 bg-gray-700/50 rounded-lg text-center"
            >
              <div className="w-10 h-10 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                <Cpu className="w-5 h-5 text-purple-400" />
              </div>
              <div className="text-sm font-medium text-white capitalize">{agent}</div>
            </div>
          ))}
        </div>
      </div>

      {/* System Status */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-green-400" />
          System Status
        </h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-400">API Status</span>
            <span className="flex items-center gap-2 text-green-400">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              Operational
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Multi-Agent System</span>
            <span className="text-green-400">Active</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Workflow Engine</span>
            <span className="text-green-400">Ready</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Vector Memory</span>
            <span className="text-green-400">Connected</span>
          </div>
        </div>
      </div>
    </div>
  );
}
