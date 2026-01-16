'use client';

import { useState, useEffect } from 'react';
import {
  Plus, Play, Save, Trash2, ChevronRight, Settings,
  Search, Globe, Code, FileText, Terminal, Zap
} from 'lucide-react';
import {
  listWorkflows, createWorkflow, runWorkflow, deleteWorkflow,
  getWorkflowTemplates, listTools
} from '@/lib/api';
import { Workflow, WorkflowStep, Tool } from '@/lib/types';

const stepTypeIcons: Record<string, React.ReactNode> = {
  tool: <Zap className="w-4 h-4" />,
  agent: <Settings className="w-4 h-4" />,
  condition: <ChevronRight className="w-4 h-4" />,
  loop: <ChevronRight className="w-4 h-4" />,
  parallel: <ChevronRight className="w-4 h-4" />
};

export default function WorkflowBuilder() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [templates, setTemplates] = useState<Workflow[]>([]);
  const [tools, setTools] = useState<Tool[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newWorkflow, setNewWorkflow] = useState({
    name: '',
    description: '',
    steps: [] as WorkflowStep[],
    variables: {},
    tags: [] as string[]
  });
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [workflowsRes, templatesRes, toolsRes] = await Promise.all([
        listWorkflows(),
        getWorkflowTemplates(),
        listTools()
      ]);
      setWorkflows(workflowsRes.workflows || []);
      setTemplates(templatesRes.templates || []);
      setTools(toolsRes.tools || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkflow = async () => {
    if (!newWorkflow.name) return;

    try {
      await createWorkflow(newWorkflow);
      await loadData();
      setIsCreating(false);
      setNewWorkflow({ name: '', description: '', steps: [], variables: {}, tags: [] });
    } catch (err) {
      console.error('Failed to create workflow:', err);
    }
  };

  const handleRunWorkflow = async (id: string) => {
    setRunning(id);
    try {
      const result = await runWorkflow(id);
      alert(`Workflow completed: ${result.status}`);
    } catch (err) {
      console.error('Failed to run workflow:', err);
    } finally {
      setRunning(null);
    }
  };

  const handleDeleteWorkflow = async (id: string) => {
    if (!confirm('Delete this workflow?')) return;
    try {
      await deleteWorkflow(id);
      await loadData();
      if (selectedWorkflow?.id === id) {
        setSelectedWorkflow(null);
      }
    } catch (err) {
      console.error('Failed to delete workflow:', err);
    }
  };

  const addStep = (type: string) => {
    const step: WorkflowStep = {
      id: `step_${Date.now()}`,
      name: `New ${type} Step`,
      type: type as any,
      config: type === 'tool' ? { tool: tools[0]?.name || '' } : {}
    };
    setNewWorkflow({
      ...newWorkflow,
      steps: [...newWorkflow.steps, step]
    });
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Workflow Builder</h2>
        <button
          onClick={() => setIsCreating(true)}
          className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Workflow
        </button>
      </div>

      {/* Templates */}
      {templates.length > 0 && (
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <h3 className="text-lg font-medium text-white mb-3">Templates</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {templates.map((template) => (
              <div
                key={template.id}
                className="p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 cursor-pointer"
                onClick={() => {
                  setNewWorkflow({
                    name: template.name + ' Copy',
                    description: template.description,
                    steps: template.steps,
                    variables: template.variables || {},
                    tags: template.tags
                  });
                  setIsCreating(true);
                }}
              >
                <div className="font-medium text-white">{template.name}</div>
                <div className="text-sm text-gray-400">{template.description}</div>
                <div className="text-xs text-gray-500 mt-1">{template.steps?.length || 0} steps</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Create Form */}
      {isCreating && (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-lg font-medium text-white mb-4">Create Workflow</h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Name</label>
              <input
                type="text"
                value={newWorkflow.name}
                onChange={(e) => setNewWorkflow({ ...newWorkflow, name: e.target.value })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white"
                placeholder="My Workflow"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Description</label>
              <textarea
                value={newWorkflow.description}
                onChange={(e) => setNewWorkflow({ ...newWorkflow, description: e.target.value })}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white"
                rows={2}
                placeholder="What does this workflow do?"
              />
            </div>

            {/* Steps */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-gray-400">Steps</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => addStep('tool')}
                    className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded"
                  >
                    + Tool
                  </button>
                  <button
                    onClick={() => addStep('agent')}
                    className="px-2 py-1 text-xs bg-purple-600 hover:bg-purple-700 text-white rounded"
                  >
                    + Agent
                  </button>
                </div>
              </div>

              {newWorkflow.steps.length === 0 ? (
                <div className="text-center py-8 text-gray-500 bg-gray-900/50 rounded-lg">
                  No steps yet. Add a tool or agent step to get started.
                </div>
              ) : (
                <div className="space-y-2">
                  {newWorkflow.steps.map((step, idx) => (
                    <div
                      key={step.id}
                      className="flex items-center gap-3 p-3 bg-gray-900/50 rounded-lg"
                    >
                      <div className="w-6 h-6 bg-gray-700 rounded-full flex items-center justify-center text-xs text-white">
                        {idx + 1}
                      </div>
                      <div className="flex-1">
                        <input
                          type="text"
                          value={step.name}
                          onChange={(e) => {
                            const steps = [...newWorkflow.steps];
                            steps[idx].name = e.target.value;
                            setNewWorkflow({ ...newWorkflow, steps });
                          }}
                          className="bg-transparent border-none text-white w-full focus:outline-none"
                        />
                        <div className="text-xs text-gray-500">{step.type}</div>
                      </div>
                      {step.type === 'tool' && (
                        <select
                          value={step.config.tool || ''}
                          onChange={(e) => {
                            const steps = [...newWorkflow.steps];
                            steps[idx].config.tool = e.target.value;
                            setNewWorkflow({ ...newWorkflow, steps });
                          }}
                          className="px-2 py-1 bg-gray-700 text-white text-sm rounded"
                        >
                          {tools.map((t) => (
                            <option key={t.name} value={t.name}>{t.name}</option>
                          ))}
                        </select>
                      )}
                      <button
                        onClick={() => {
                          const steps = newWorkflow.steps.filter((_, i) => i !== idx);
                          setNewWorkflow({ ...newWorkflow, steps });
                        }}
                        className="p-1 text-gray-500 hover:text-red-400"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleCreateWorkflow}
                disabled={!newWorkflow.name}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-lg flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save Workflow
              </button>
              <button
                onClick={() => {
                  setIsCreating(false);
                  setNewWorkflow({ name: '', description: '', steps: [], variables: {}, tags: [] });
                }}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Existing Workflows */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-medium text-white mb-4">Your Workflows</h3>

        {workflows.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No workflows yet. Create one to get started!
          </div>
        ) : (
          <div className="space-y-3">
            {workflows.map((workflow) => (
              <div
                key={workflow.id}
                className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg"
              >
                <div>
                  <div className="font-medium text-white">{workflow.name}</div>
                  <div className="text-sm text-gray-400">{workflow.description}</div>
                  <div className="flex gap-2 mt-1">
                    {workflow.tags?.map((tag) => (
                      <span key={tag} className="text-xs px-2 py-0.5 bg-gray-600 rounded text-gray-300">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleRunWorkflow(workflow.id)}
                    disabled={running === workflow.id}
                    className="p-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded-lg"
                  >
                    {running === workflow.id ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                  </button>
                  <button
                    onClick={() => handleDeleteWorkflow(workflow.id)}
                    className="p-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
