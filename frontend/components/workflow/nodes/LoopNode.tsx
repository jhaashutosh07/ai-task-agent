'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Repeat, CheckCircle, XCircle, Loader2 } from 'lucide-react';

export interface LoopNodeData {
  label: string;
  iterateOver: string;
  description?: string;
  maxIterations?: number;
  status?: 'idle' | 'running' | 'success' | 'error';
  currentIteration?: number;
  totalIterations?: number;
}

function LoopNode({ data, selected }: NodeProps<LoopNodeData>) {
  const statusIcon = {
    idle: null,
    running: <Loader2 className="w-4 h-4 animate-spin text-teal-400" />,
    success: <CheckCircle className="w-4 h-4 text-green-400" />,
    error: <XCircle className="w-4 h-4 text-red-400" />,
  };

  const progress =
    data.totalIterations && data.currentIteration
      ? (data.currentIteration / data.totalIterations) * 100
      : 0;

  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-[180px] transition-all ${
        selected
          ? 'border-teal-500 bg-teal-500/20 shadow-lg shadow-teal-500/20'
          : 'border-gray-600 bg-gray-800 hover:border-gray-500'
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-teal-500 !w-3 !h-3 !border-2 !border-gray-800"
      />

      <div className="flex items-center gap-2 mb-1">
        <div className="p-1.5 bg-teal-500/20 rounded">
          <Repeat className="w-4 h-4 text-teal-400" />
        </div>
        <span className="text-xs text-teal-400 font-medium uppercase">Loop</span>
        {data.status && statusIcon[data.status]}
      </div>

      <div className="font-medium text-white">{data.label}</div>

      {data.description && (
        <div className="text-xs text-gray-400 mt-1 line-clamp-2">{data.description}</div>
      )}

      {data.iterateOver && (
        <div className="mt-2 px-2 py-1 bg-gray-700/50 rounded text-xs text-gray-300">
          <span className="text-gray-500">Iterate: </span>
          <span className="font-mono">{data.iterateOver}</span>
        </div>
      )}

      {data.maxIterations && (
        <div className="mt-1 text-xs text-gray-400">
          Max: {data.maxIterations} iterations
        </div>
      )}

      {data.status === 'running' && data.totalIterations && (
        <div className="mt-2">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Progress</span>
            <span>
              {data.currentIteration}/{data.totalIterations}
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-1.5">
            <div
              className="bg-teal-500 h-1.5 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Loop body output */}
      <Handle
        type="source"
        position={Position.Right}
        id="loop-body"
        className="!bg-teal-500 !w-3 !h-3 !border-2 !border-gray-800"
      />

      {/* Exit output */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="exit"
        className="!bg-gray-500 !w-3 !h-3 !border-2 !border-gray-800"
      />

      <div className="flex justify-between mt-3 text-xs">
        <span className="text-gray-400">Exit</span>
        <span className="text-teal-400">Loop</span>
      </div>
    </div>
  );
}

export default memo(LoopNode);
