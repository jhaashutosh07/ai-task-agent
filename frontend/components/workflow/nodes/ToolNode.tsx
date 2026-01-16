'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Wrench, Play, CheckCircle, XCircle, Loader2 } from 'lucide-react';

export interface ToolNodeData {
  label: string;
  tool: string;
  description?: string;
  config?: Record<string, any>;
  status?: 'idle' | 'running' | 'success' | 'error';
  output?: string;
}

function ToolNode({ data, selected }: NodeProps<ToolNodeData>) {
  const statusIcon = {
    idle: null,
    running: <Loader2 className="w-4 h-4 animate-spin text-blue-400" />,
    success: <CheckCircle className="w-4 h-4 text-green-400" />,
    error: <XCircle className="w-4 h-4 text-red-400" />,
  };

  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-[180px] transition-all ${
        selected
          ? 'border-blue-500 bg-blue-500/20 shadow-lg shadow-blue-500/20'
          : 'border-gray-600 bg-gray-800 hover:border-gray-500'
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-blue-500 !w-3 !h-3 !border-2 !border-gray-800"
      />

      <div className="flex items-center gap-2 mb-1">
        <div className="p-1.5 bg-blue-500/20 rounded">
          <Wrench className="w-4 h-4 text-blue-400" />
        </div>
        <span className="text-xs text-blue-400 font-medium uppercase">Tool</span>
        {data.status && statusIcon[data.status]}
      </div>

      <div className="font-medium text-white">{data.label}</div>

      {data.description && (
        <div className="text-xs text-gray-400 mt-1 line-clamp-2">{data.description}</div>
      )}

      {data.tool && (
        <div className="mt-2 px-2 py-1 bg-gray-700/50 rounded text-xs text-gray-300 font-mono">
          {data.tool}
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
        className="!bg-blue-500 !w-3 !h-3 !border-2 !border-gray-800"
      />
    </div>
  );
}

export default memo(ToolNode);
