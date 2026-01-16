'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
  Panel,
  ReactFlowProvider,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  Plus,
  Play,
  Save,
  Download,
  Upload,
  Wrench,
  Bot,
  GitBranch,
  Repeat,
  Trash2,
  Undo,
  Redo,
} from 'lucide-react';
import { ToolNode, AgentNode, ConditionNode, LoopNode } from './nodes';
import NodeConfigPanel from './NodeConfigPanel';
import ExecutionOverlay from './ExecutionOverlay';

const nodeTypes = {
  tool: ToolNode,
  agent: AgentNode,
  condition: ConditionNode,
  loop: LoopNode,
};

interface WorkflowCanvasProps {
  workflowId?: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  tools: Array<{ name: string; description: string }>;
  agents: string[];
  onSave?: (nodes: Node[], edges: Edge[]) => void;
  onRun?: (nodes: Node[], edges: Edge[]) => Promise<void>;
}

let nodeId = 0;
const getNodeId = () => `node_${nodeId++}`;

function WorkflowCanvasInner({
  workflowId,
  initialNodes = [],
  initialEdges = [],
  tools,
  agents,
  onSave,
  onRun,
}: WorkflowCanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { project } = useReactFlow();

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [showConfig, setShowConfig] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [executionSteps, setExecutionSteps] = useState<any[]>([]);
  const [showExecution, setShowExecution] = useState(false);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    setShowConfig(true);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setShowConfig(false);
  }, []);

  const addNode = useCallback(
    (type: string) => {
      const newNode: Node = {
        id: getNodeId(),
        type,
        position: { x: 250, y: 250 },
        data: {
          label: `New ${type.charAt(0).toUpperCase() + type.slice(1)}`,
          ...(type === 'tool' && { tool: '' }),
          ...(type === 'agent' && { agent: '', prompt: '' }),
          ...(type === 'condition' && { condition: '' }),
          ...(type === 'loop' && { iterateOver: '', maxIterations: 100 }),
        },
      };
      setNodes((nds) => [...nds, newNode]);
    },
    [setNodes]
  );

  const updateNode = useCallback(
    (nodeId: string, data: any) => {
      setNodes((nds) =>
        nds.map((node) => (node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node))
      );
      setShowConfig(false);
    },
    [setNodes]
  );

  const deleteNode = useCallback(
    (nodeId: string) => {
      setNodes((nds) => nds.filter((node) => node.id !== nodeId));
      setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    },
    [setNodes, setEdges]
  );

  const handleSave = useCallback(() => {
    if (onSave) {
      onSave(nodes, edges);
    }
  }, [nodes, edges, onSave]);

  const handleRun = useCallback(async () => {
    if (!onRun) return;

    setIsRunning(true);
    setShowExecution(true);
    setExecutionSteps(
      nodes.map((node) => ({
        nodeId: node.id,
        nodeName: node.data.label,
        status: 'pending',
      }))
    );

    // Update node statuses during execution
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: 'idle' },
      }))
    );

    try {
      await onRun(nodes, edges);
    } finally {
      setIsRunning(false);
    }
  }, [nodes, edges, onRun, setNodes]);

  const handleStop = useCallback(() => {
    setIsRunning(false);
  }, []);

  const handleExport = useCallback(() => {
    const workflow = {
      nodes,
      edges,
      exportedAt: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(workflow, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow-${workflowId || 'export'}.json`;
    a.click();
  }, [nodes, edges, workflowId]);

  const handleImport = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const workflow = JSON.parse(e.target?.result as string);
            if (workflow.nodes) setNodes(workflow.nodes);
            if (workflow.edges) setEdges(workflow.edges);
          } catch (err) {
            console.error('Failed to import workflow:', err);
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  }, [setNodes, setEdges]);

  return (
    <div className="w-full h-full flex">
      <div ref={reactFlowWrapper} className="flex-1 h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          fitView
          className="bg-gray-900"
          defaultEdgeOptions={{
            animated: true,
            style: { stroke: '#4b5563', strokeWidth: 2 },
          }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#374151" />
          <Controls className="!bg-gray-800 !border-gray-700 !rounded-lg overflow-hidden [&>button]:!bg-gray-800 [&>button]:!border-gray-700 [&>button]:!text-gray-400 [&>button:hover]:!bg-gray-700" />
          <MiniMap
            className="!bg-gray-800 !border-gray-700 !rounded-lg"
            nodeColor={(node) => {
              switch (node.type) {
                case 'tool':
                  return '#3b82f6';
                case 'agent':
                  return '#a855f7';
                case 'condition':
                  return '#f59e0b';
                case 'loop':
                  return '#14b8a6';
                default:
                  return '#6b7280';
              }
            }}
          />

          {/* Toolbar */}
          <Panel position="top-left" className="flex gap-2">
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-1 flex gap-1">
              <button
                onClick={() => addNode('tool')}
                className="p-2 hover:bg-gray-700 rounded text-blue-400 transition-colors"
                title="Add Tool Node"
              >
                <Wrench className="w-5 h-5" />
              </button>
              <button
                onClick={() => addNode('agent')}
                className="p-2 hover:bg-gray-700 rounded text-purple-400 transition-colors"
                title="Add Agent Node"
              >
                <Bot className="w-5 h-5" />
              </button>
              <button
                onClick={() => addNode('condition')}
                className="p-2 hover:bg-gray-700 rounded text-amber-400 transition-colors"
                title="Add Condition Node"
              >
                <GitBranch className="w-5 h-5" />
              </button>
              <button
                onClick={() => addNode('loop')}
                className="p-2 hover:bg-gray-700 rounded text-teal-400 transition-colors"
                title="Add Loop Node"
              >
                <Repeat className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-gray-800 border border-gray-700 rounded-lg p-1 flex gap-1">
              <button
                onClick={handleRun}
                disabled={isRunning || nodes.length === 0}
                className="p-2 hover:bg-gray-700 rounded text-green-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Run Workflow"
              >
                <Play className="w-5 h-5" />
              </button>
              <button
                onClick={handleSave}
                className="p-2 hover:bg-gray-700 rounded text-white transition-colors"
                title="Save Workflow"
              >
                <Save className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-gray-800 border border-gray-700 rounded-lg p-1 flex gap-1">
              <button
                onClick={handleExport}
                className="p-2 hover:bg-gray-700 rounded text-gray-400 transition-colors"
                title="Export Workflow"
              >
                <Download className="w-5 h-5" />
              </button>
              <button
                onClick={handleImport}
                className="p-2 hover:bg-gray-700 rounded text-gray-400 transition-colors"
                title="Import Workflow"
              >
                <Upload className="w-5 h-5" />
              </button>
            </div>
          </Panel>

          {/* Node count */}
          <Panel position="bottom-left" className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2">
            <span className="text-sm text-gray-400">
              {nodes.length} nodes, {edges.length} connections
            </span>
          </Panel>
        </ReactFlow>
      </div>

      {/* Config Panel */}
      {showConfig && selectedNode && (
        <NodeConfigPanel
          node={selectedNode}
          tools={tools}
          agents={agents}
          onUpdate={updateNode}
          onDelete={deleteNode}
          onClose={() => setShowConfig(false)}
        />
      )}

      {/* Execution Overlay */}
      {showExecution && (
        <ExecutionOverlay
          isRunning={isRunning}
          steps={executionSteps}
          onStop={handleStop}
          onClose={() => setShowExecution(false)}
        />
      )}
    </div>
  );
}

export default function WorkflowCanvas(props: WorkflowCanvasProps) {
  return (
    <ReactFlowProvider>
      <WorkflowCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
