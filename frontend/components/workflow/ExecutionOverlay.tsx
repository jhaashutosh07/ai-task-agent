'use client';

import { useState, useEffect } from 'react';
import { Play, Square, Clock, CheckCircle, XCircle, Loader2, ChevronDown, ChevronUp } from 'lucide-react';

interface ExecutionStep {
  nodeId: string;
  nodeName: string;
  status: 'pending' | 'running' | 'success' | 'error';
  output?: string;
  error?: string;
  startTime?: Date;
  endTime?: Date;
}

interface ExecutionOverlayProps {
  isRunning: boolean;
  executionId?: string;
  steps: ExecutionStep[];
  onStop: () => void;
  onClose: () => void;
}

export default function ExecutionOverlay({
  isRunning,
  executionId,
  steps,
  onStop,
  onClose,
}: ExecutionOverlayProps) {
  const [expanded, setExpanded] = useState(true);
  const [selectedStep, setSelectedStep] = useState<ExecutionStep | null>(null);

  const completedSteps = steps.filter((s) => s.status === 'success').length;
  const failedSteps = steps.filter((s) => s.status === 'error').length;
  const currentStep = steps.find((s) => s.status === 'running');

  const progress = steps.length > 0 ? (completedSteps / steps.length) * 100 : 0;

  const getStatusIcon = (status: ExecutionStep['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-gray-500" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-400" />;
    }
  };

  const formatDuration = (start?: Date, end?: Date) => {
    if (!start) return '-';
    const endTime = end || new Date();
    const ms = endTime.getTime() - start.getTime();
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <div className="fixed bottom-4 right-4 w-96 bg-gray-800 rounded-xl shadow-2xl border border-gray-700 overflow-hidden z-50">
      {/* Header */}
      <div
        className="p-4 border-b border-gray-700 flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          {isRunning ? (
            <div className="relative">
              <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
            </div>
          ) : failedSteps > 0 ? (
            <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
              <XCircle className="w-5 h-5 text-red-400" />
            </div>
          ) : (
            <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
          )}
          <div>
            <div className="font-medium text-white">
              {isRunning ? 'Executing Workflow' : failedSteps > 0 ? 'Execution Failed' : 'Execution Complete'}
            </div>
            <div className="text-xs text-gray-400">
              {completedSteps}/{steps.length} steps completed
              {failedSteps > 0 && ` (${failedSteps} failed)`}
            </div>
          </div>
        </div>
        <button className="text-gray-400 hover:text-white transition-colors">
          {expanded ? <ChevronDown className="w-5 h-5" /> : <ChevronUp className="w-5 h-5" />}
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-gray-700">
        <div
          className={`h-full transition-all duration-300 ${
            failedSteps > 0 ? 'bg-red-500' : 'bg-blue-500'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Steps list */}
      {expanded && (
        <div className="max-h-64 overflow-y-auto">
          {steps.map((step, index) => (
            <div
              key={step.nodeId}
              className={`p-3 border-b border-gray-700/50 cursor-pointer transition-colors ${
                selectedStep?.nodeId === step.nodeId
                  ? 'bg-gray-700/50'
                  : 'hover:bg-gray-700/30'
              }`}
              onClick={() => setSelectedStep(selectedStep?.nodeId === step.nodeId ? null : step)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-5">{index + 1}</span>
                  {getStatusIcon(step.status)}
                  <span className="text-sm text-white">{step.nodeName}</span>
                </div>
                <span className="text-xs text-gray-500">
                  {formatDuration(step.startTime, step.endTime)}
                </span>
              </div>

              {/* Expanded step details */}
              {selectedStep?.nodeId === step.nodeId && (
                <div className="mt-2 pl-7">
                  {step.output && (
                    <div className="bg-gray-900/50 rounded p-2 text-xs text-gray-300 font-mono max-h-20 overflow-auto">
                      {step.output}
                    </div>
                  )}
                  {step.error && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded p-2 text-xs text-red-400 mt-1">
                      {step.error}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      {expanded && (
        <div className="p-3 border-t border-gray-700 flex gap-2">
          {isRunning ? (
            <button
              onClick={onStop}
              className="flex-1 flex items-center justify-center gap-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 px-4 py-2 rounded-lg transition-colors"
            >
              <Square className="w-4 h-4" />
              Stop Execution
            </button>
          ) : (
            <button
              onClick={onClose}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Close
            </button>
          )}
        </div>
      )}
    </div>
  );
}
