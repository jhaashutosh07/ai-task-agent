'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Bot, CheckCircle, XCircle, Loader2 } from 'lucide-react';

export interface AgentNodeData {
  label: string;
  agent: string;
  description?: string;
  prompt?: string;
  status?: 'idle' | 'running' | 'success' | 'error';
  output?: string;
}

const agentColors: Record<string, string> = {
  orchestrator: 'purple',
  researcher: 'cyan',
  coder: 'green',
  analyst: 'yellow',
  executor: 'orange',
};

function AgentNode({ data, selected }: NodeProps<AgentNodeData>) {
  const color = agentColors[data.agent] || 'purple';

  const statusIcon = {
    idle: null,
    running: <Loader2 className="w-4 h-4 animate-spin text-purple-400" />,
    success: <CheckCircle className="w-4 h-4 text-green-400" />,
    error: <XCircle className="w-4 h-4 text-red-400" />,
  };

  const colorClasses: Record<string, { border: string; bg: string; text: string; icon: string }> = {
    purple: {
      border: 'border-purple-500',
      bg: 'bg-purple-500/20',
      text: 'text-purple-400',
      icon: 'bg-purple-500/20',
    },
    cyan: {
      border: 'border-cyan-500',
      bg: 'bg-cyan-500/20',
      text: 'text-cyan-400',
      icon: 'bg-cyan-500/20',
    },
    green: {
      border: 'border-green-500',
      bg: 'bg-green-500/20',
      text: 'text-green-400',
      icon: 'bg-green-500/20',
    },
    yellow: {
      border: 'border-yellow-500',
      bg: 'bg-yellow-500/20',
      text: 'text-yellow-400',
      icon: 'bg-yellow-500/20',
    },
    orange: {
      border: 'border-orange-500',
      bg: 'bg-orange-500/20',
      text: 'text-orange-400',
      icon: 'bg-orange-500/20',
    },
  };

  const colors = colorClasses[color] || colorClasses.purple;

  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-[200px] transition-all ${
        selected
          ? `${colors.border} ${colors.bg} shadow-lg`
          : `border-gray-600 bg-gray-800 hover:border-gray-500`
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-purple-500 !w-3 !h-3 !border-2 !border-gray-800"
      />

      <div className="flex items-center gap-2 mb-1">
        <div className={`p-1.5 ${colors.icon} rounded`}>
          <Bot className={`w-4 h-4 ${colors.text}`} />
        </div>
        <span className={`text-xs ${colors.text} font-medium uppercase`}>Agent</span>
        {data.status && statusIcon[data.status]}
      </div>

      <div className="font-medium text-white">{data.label}</div>

      {data.description && (
        <div className="text-xs text-gray-400 mt-1 line-clamp-2">{data.description}</div>
      )}

      <div className={`mt-2 px-2 py-1 ${colors.bg} rounded text-xs ${colors.text} font-medium capitalize`}>
        {data.agent}
      </div>

      {data.prompt && (
        <div className="mt-2 px-2 py-1 bg-gray-700/50 rounded text-xs text-gray-300 line-clamp-2">
          {data.prompt}
        </div>
      )}

      {data.output && data.status === 'success' && (
        <div className="mt-2 px-2 py-1 bg-green-500/10 border border-green-500/30 rounded text-xs text-green-400 line-clamp-2">
          {data.output}
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-purple-500 !w-3 !h-3 !border-2 !border-gray-800"
      />
    </div>
  );
}

export default memo(AgentNode);
