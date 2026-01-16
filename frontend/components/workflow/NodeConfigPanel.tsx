'use client';

import { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import { X, Settings, Wrench, Bot, GitBranch, Repeat, Save, Trash2 } from 'lucide-react';

interface NodeConfigPanelProps {
  node: Node | null;
  tools: Array<{ name: string; description: string }>;
  agents: string[];
  onUpdate: (nodeId: string, data: any) => void;
  onDelete: (nodeId: string) => void;
  onClose: () => void;
}

export default function NodeConfigPanel({
  node,
  tools,
  agents,
  onUpdate,
  onDelete,
  onClose,
}: NodeConfigPanelProps) {
  const [formData, setFormData] = useState<Record<string, any>>({});

  useEffect(() => {
    if (node) {
      setFormData(node.data);
    }
  }, [node]);

  if (!node) return null;

  const handleSave = () => {
    onUpdate(node.id, formData);
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this node?')) {
      onDelete(node.id);
      onClose();
    }
  };

  const nodeTypeConfig: Record<string, { icon: any; color: string; title: string }> = {
    tool: { icon: Wrench, color: 'blue', title: 'Tool Configuration' },
    agent: { icon: Bot, color: 'purple', title: 'Agent Configuration' },
    condition: { icon: GitBranch, color: 'amber', title: 'Condition Configuration' },
    loop: { icon: Repeat, color: 'teal', title: 'Loop Configuration' },
  };

  const config = nodeTypeConfig[node.type || 'tool'] || nodeTypeConfig.tool;
  const Icon = config.icon;

  return (
    <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={`w-5 h-5 text-${config.color}-400`} />
          <h3 className="font-medium text-white">{config.title}</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Label */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Label</label>
          <input
            type="text"
            value={formData.label || ''}
            onChange={(e) => setFormData({ ...formData, label: e.target.value })}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Node label"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
          <textarea
            value={formData.description || ''}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[80px] resize-none"
            placeholder="Optional description"
          />
        </div>

        {/* Tool-specific fields */}
        {node.type === 'tool' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Tool</label>
              <select
                value={formData.tool || ''}
                onChange={(e) => setFormData({ ...formData, tool: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a tool</option>
                {tools.map((tool) => (
                  <option key={tool.name} value={tool.name}>
                    {tool.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Parameters (JSON)
              </label>
              <textarea
                value={
                  formData.config ? JSON.stringify(formData.config, null, 2) : ''
                }
                onChange={(e) => {
                  try {
                    const config = JSON.parse(e.target.value);
                    setFormData({ ...formData, config });
                  } catch {
                    // Invalid JSON, ignore
                  }
                }}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[100px] resize-none"
                placeholder="{}"
              />
            </div>
          </>
        )}

        {/* Agent-specific fields */}
        {node.type === 'agent' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Agent</label>
              <select
                value={formData.agent || ''}
                onChange={(e) => setFormData({ ...formData, agent: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select an agent</option>
                {agents.map((agent) => (
                  <option key={agent} value={agent}>
                    {agent.charAt(0).toUpperCase() + agent.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Prompt</label>
              <textarea
                value={formData.prompt || ''}
                onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[100px] resize-none"
                placeholder="Task prompt for the agent"
              />
            </div>
          </>
        )}

        {/* Condition-specific fields */}
        {node.type === 'condition' && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Condition</label>
            <textarea
              value={formData.condition || ''}
              onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[80px] resize-none"
              placeholder="result.success === true"
            />
            <p className="text-xs text-gray-500 mt-1">
              JavaScript expression that evaluates to true/false
            </p>
          </div>
        )}

        {/* Loop-specific fields */}
        {node.type === 'loop' && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Iterate Over</label>
              <input
                type="text"
                value={formData.iterateOver || ''}
                onChange={(e) => setFormData({ ...formData, iterateOver: e.target.value })}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="context.items"
              />
              <p className="text-xs text-gray-500 mt-1">
                Variable containing an array to iterate over
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Max Iterations
              </label>
              <input
                type="number"
                value={formData.maxIterations || 100}
                onChange={(e) =>
                  setFormData({ ...formData, maxIterations: parseInt(e.target.value) })
                }
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                min={1}
                max={1000}
              />
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700 flex gap-2">
        <button
          onClick={handleSave}
          className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <Save className="w-4 h-4" />
          Save
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center justify-center gap-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 px-4 py-2 rounded-lg transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
