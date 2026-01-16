'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Search,
  GitBranch,
  Clock,
  Play,
  Trash2,
  FileText,
  LayoutTemplate,
} from 'lucide-react';
import { listWorkflows, deleteWorkflow, runWorkflow, getWorkflowTemplates } from '@/lib/api';
import { TemplateGallery } from '@/components/workflow';

interface Workflow {
  id: string;
  name: string;
  description: string;
  steps_count: number;
  tags: string[];
  updated_at: string | null;
}

export default function WorkflowsPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [showTemplates, setShowTemplates] = useState(false);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const data = await listWorkflows();
      setWorkflows(data.workflows || []);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this workflow?')) return;

    try {
      await deleteWorkflow(id);
      setWorkflows((prev) => prev.filter((w) => w.id !== id));
    } catch (error) {
      console.error('Failed to delete workflow:', error);
    }
  };

  const handleRun = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await runWorkflow(id);
      alert('Workflow started successfully!');
    } catch (error) {
      console.error('Failed to run workflow:', error);
      alert('Failed to run workflow');
    }
  };

  const handleTemplateSelect = (template: any) => {
    // Navigate to editor with template data
    const params = new URLSearchParams({
      template: JSON.stringify({
        nodes: template.nodes,
        edges: template.edges,
        name: template.name,
        description: template.description,
      }),
    });
    router.push(`/workflows/new?${params.toString()}`);
    setShowTemplates(false);
  };

  const filteredWorkflows = workflows.filter(
    (w) =>
      w.name.toLowerCase().includes(search.toLowerCase()) ||
      w.description.toLowerCase().includes(search.toLowerCase())
  );

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Workflows</h1>
          <p className="text-gray-400 mt-1">Create and manage automated workflows</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowTemplates(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            <LayoutTemplate className="w-5 h-5" />
            Templates
          </button>
          <button
            onClick={() => router.push('/workflows/new')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Plus className="w-5 h-5" />
            New Workflow
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg py-2.5 pl-10 pr-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Search workflows..."
        />
      </div>

      {/* Workflows grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-gray-800 rounded-xl p-4 animate-pulse">
              <div className="h-6 bg-gray-700 rounded w-3/4 mb-2" />
              <div className="h-4 bg-gray-700 rounded w-full mb-4" />
              <div className="h-4 bg-gray-700 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : filteredWorkflows.length === 0 ? (
        <div className="text-center py-16">
          <GitBranch className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-white mb-2">No workflows yet</h3>
          <p className="text-gray-400 mb-6">
            Create your first workflow to automate complex tasks
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => setShowTemplates(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              <LayoutTemplate className="w-5 h-5" />
              Browse Templates
            </button>
            <button
              onClick={() => router.push('/workflows/new')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <Plus className="w-5 h-5" />
              Create Workflow
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredWorkflows.map((workflow) => (
            <div
              key={workflow.id}
              onClick={() => router.push(`/workflows/${workflow.id}`)}
              className="bg-gray-800 border border-gray-700 rounded-xl p-4 cursor-pointer hover:border-blue-500 transition-all group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-500/20 rounded-lg group-hover:bg-blue-500/30 transition-colors">
                    <GitBranch className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-white group-hover:text-blue-400 transition-colors">
                      {workflow.name}
                    </h3>
                    <span className="text-xs text-gray-500">
                      {workflow.steps_count} steps
                    </span>
                  </div>
                </div>
              </div>

              {workflow.description && (
                <p className="text-sm text-gray-400 mb-3 line-clamp-2">
                  {workflow.description}
                </p>
              )}

              {/* Tags */}
              {workflow.tags && workflow.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {workflow.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 bg-gray-700 rounded text-xs text-gray-300"
                    >
                      {tag}
                    </span>
                  ))}
                  {workflow.tags.length > 3 && (
                    <span className="px-2 py-0.5 bg-gray-700 rounded text-xs text-gray-400">
                      +{workflow.tags.length - 3}
                    </span>
                  )}
                </div>
              )}

              <div className="flex items-center justify-between pt-3 border-t border-gray-700">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <Clock className="w-3.5 h-3.5" />
                  {formatDate(workflow.updated_at)}
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => handleRun(workflow.id, e)}
                    className="p-1.5 hover:bg-green-500/20 rounded text-green-400 transition-colors"
                    title="Run workflow"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(workflow.id, e)}
                    className="p-1.5 hover:bg-red-500/20 rounded text-red-400 transition-colors"
                    title="Delete workflow"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Template Gallery Modal */}
      {showTemplates && (
        <TemplateGallery
          onSelect={handleTemplateSelect}
          onClose={() => setShowTemplates(false)}
        />
      )}
    </div>
  );
}
