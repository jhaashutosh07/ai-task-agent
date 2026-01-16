'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { GitBranch, CheckCircle, XCircle, Loader2 } from 'lucide-react';

export interface ConditionNodeData {
  label: string;
  condition: string;
  description?: string;
  status?: 'idle' | 'running' | 'success' | 'error';
  result?: boolean;
}

function ConditionNode({ data, selected }: NodeProps<ConditionNodeData>) {
  const statusIcon = {
    idle: null,
    running: <Loader2 className="w-4 h-4 animate-spin text-amber-400" />,
    success: <CheckCircle className="w-4 h-4 text-green-400" />,
    error: <XCircle className="w-4 h-4 text-red-400" />,
  };

  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-[180px] transition-all ${
        selected
          ? 'border-amber-500 bg-amber-500/20 shadow-lg shadow-amber-500/20'
          : 'border-gray-600 bg-gray-800 hover:border-gray-500'
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-amber-500 !w-3 !h-3 !border-2 !border-gray-800"
      />

      <div className="flex items-center gap-2 mb-1">
        <div className="p-1.5 bg-amber-500/20 rounded">
          <GitBranch className="w-4 h-4 text-amber-400" />
        </div>
        <span className="text-xs text-amber-400 font-medium uppercase">Condition</span>
        {data.status && statusIcon[data.status]}
      </div>

      <div className="font-medium text-white">{data.label}</div>

      {data.description && (
        <div className="text-xs text-gray-400 mt-1 line-clamp-2">{data.description}</div>
      )}

      {data.condition && (
        <div className="mt-2 px-2 py-1 bg-gray-700/50 rounded text-xs text-gray-300 font-mono">
          {data.condition}
        </div>
      )}

      {data.status === 'success' && data.result !== undefined && (
        <div
          className={`mt-2 px-2 py-1 rounded text-xs font-medium ${
            data.result
              ? 'bg-green-500/10 border border-green-500/30 text-green-400'
              : 'bg-red-500/10 border border-red-500/30 text-red-400'
          }`}
        >
          Result: {data.result ? 'True' : 'False'}
        </div>
      )}

      {/* True output */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="true"
        style={{ left: '30%' }}
        className="!bg-green-500 !w-3 !h-3 !border-2 !border-gray-800"
      />

      {/* False output */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="false"
        style={{ left: '70%' }}
        className="!bg-red-500 !w-3 !h-3 !border-2 !border-gray-800"
      />

      <div className="flex justify-between mt-3 text-xs px-2">
        <span className="text-green-400">True</span>
        <span className="text-red-400">False</span>
      </div>
    </div>
  );
}

export default memo(ConditionNode);
