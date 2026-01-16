'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import { Node, Edge } from 'reactflow';
import { WorkflowCanvas } from '@/components/workflow';
import { getWorkflow, createWorkflow, listTools, runWorkflow } from '@/lib/api';
import { flowToWorkflow, workflowToFlow, validateWorkflow } from '@/lib/workflow-utils';

const AGENTS = ['orchestrator', 'researcher', 'coder', 'analyst', 'executor'];

export default function WorkflowEditorPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const isNew = params.id === 'new';

  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [initialNodes, setInitialNodes] = useState<Node[]>([]);
  const [initialEdges, setInitialEdges] = useState<Edge[]>([]);
  const [tools, setTools] = useState<Array<{ name: string; description: string }>>([]);

  useEffect(() => {
    loadData();
  }, [params.id]);

  const loadData = async () => {
    // Load tools list
    try {
      const toolsData = await listTools();
      setTools(toolsData.tools || []);
    } catch (error) {
      console.error('Failed to load tools:', error);
    }

    // Check for template data in URL
    const templateParam = searchParams.get('template');
    if (templateParam && isNew) {
      try {
        const template = JSON.parse(templateParam);
        setWorkflowName(template.name || 'New Workflow');
        setWorkflowDescription(template.description || '');
        setInitialNodes(template.nodes || []);
        setInitialEdges(template.edges || []);
        setLoading(false);
        return;
      } catch (e) {
        console.error('Failed to parse template:', e);
      }
    }

    // Load existing workflow
    if (!isNew) {
      try {
        const workflow = await getWorkflow(params.id as string);
        setWorkflowName(workflow.name);
        setWorkflowDescription(workflow.description || '');

        // Convert backend format to React Flow format
        const { nodes, edges } = workflowToFlow(workflow);
        setInitialNodes(nodes);
        setInitialEdges(edges);
      } catch (error) {
        console.error('Failed to load workflow:', error);
        router.push('/workflows');
      }
    }

    setLoading(false);
  };

  const handleSave = async (nodes: Node[], edges: Edge[]) => {
    // Validate workflow
    const validation = validateWorkflow(nodes, edges);
    if (!validation.valid) {
      alert('Workflow validation failed:\n' + validation.errors.join('\n'));
      return;
    }

    setSaving(true);
    try {
      const workflow = flowToWorkflow(nodes, edges, {
        name: workflowName,
        description: workflowDescription,
      });

      if (isNew) {
        const created = await createWorkflow(workflow);
        router.push(`/workflows/${created.id}`);
      } else {
        // TODO: Add update endpoint
        alert('Workflow saved!');
      }
    } catch (error) {
      console.error('Failed to save workflow:', error);
      alert('Failed to save workflow');
    } finally {
      setSaving(false);
    }
  };

  const handleRun = async (nodes: Node[], edges: Edge[]) => {
    if (isNew) {
      alert('Please save the workflow before running it.');
      return;
    }

    try {
      await runWorkflow(params.id as string);
    } catch (error) {
      console.error('Failed to run workflow:', error);
      throw error;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/workflows')}
            className="p-2 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <input
              type="text"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="bg-transparent border-none text-lg font-bold text-white focus:outline-none focus:ring-0 w-64"
              placeholder="Workflow name"
            />
            <input
              type="text"
              value={workflowDescription}
              onChange={(e) => setWorkflowDescription(e.target.value)}
              className="block bg-transparent border-none text-sm text-gray-400 focus:outline-none focus:ring-0 w-96"
              placeholder="Add a description..."
            />
          </div>
        </div>
        <div className="flex items-center gap-2">
          {saving && (
            <span className="text-sm text-gray-400 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </span>
          )}
        </div>
      </header>

      {/* Canvas */}
      <div className="flex-1">
        <WorkflowCanvas
          workflowId={isNew ? undefined : (params.id as string)}
          initialNodes={initialNodes}
          initialEdges={initialEdges}
          tools={tools}
          agents={AGENTS}
          onSave={handleSave}
          onRun={handleRun}
        />
      </div>
    </div>
  );
}
