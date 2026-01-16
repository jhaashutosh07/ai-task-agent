import { Node, Edge } from 'reactflow';

// Backend workflow step types
export type StepType = 'tool' | 'agent' | 'condition' | 'loop' | 'parallel';

export interface WorkflowStep {
  id: string;
  name: string;
  type: StepType;
  config: Record<string, any>;
  next?: string | { true: string; false: string };
}

export interface BackendWorkflow {
  id: string;
  name: string;
  description: string;
  version: number;
  steps: WorkflowStep[];
  variables: Record<string, any>;
  tags: string[];
}

/**
 * Convert React Flow nodes and edges to backend workflow format
 */
export function flowToWorkflow(
  nodes: Node[],
  edges: Edge[],
  metadata: { name: string; description: string; tags?: string[] }
): Omit<BackendWorkflow, 'id' | 'version'> {
  // Build adjacency map
  const edgeMap = new Map<string, { next?: string; true?: string; false?: string }>();

  for (const edge of edges) {
    const existing = edgeMap.get(edge.source) || {};

    if (edge.sourceHandle === 'true') {
      existing.true = edge.target;
    } else if (edge.sourceHandle === 'false') {
      existing.false = edge.target;
    } else if (edge.sourceHandle === 'loop-body') {
      existing.next = edge.target; // Loop body goes to next
    } else if (edge.sourceHandle === 'exit') {
      existing.true = edge.target; // Exit condition
    } else {
      existing.next = edge.target;
    }

    edgeMap.set(edge.source, existing);
  }

  // Convert nodes to steps
  const steps: WorkflowStep[] = nodes.map((node) => {
    const edgeInfo = edgeMap.get(node.id) || {};

    const step: WorkflowStep = {
      id: node.id,
      name: node.data.label || `Step ${node.id}`,
      type: (node.type as StepType) || 'tool',
      config: {},
    };

    // Set step-specific config
    switch (node.type) {
      case 'tool':
        step.config = {
          tool: node.data.tool,
          parameters: node.data.config || {},
        };
        if (edgeInfo.next) step.next = edgeInfo.next;
        break;

      case 'agent':
        step.config = {
          agent: node.data.agent,
          prompt: node.data.prompt,
        };
        if (edgeInfo.next) step.next = edgeInfo.next;
        break;

      case 'condition':
        step.config = {
          condition: node.data.condition,
        };
        if (edgeInfo.true || edgeInfo.false) {
          step.next = {
            true: edgeInfo.true || '',
            false: edgeInfo.false || '',
          };
        }
        break;

      case 'loop':
        step.config = {
          iterateOver: node.data.iterateOver,
          maxIterations: node.data.maxIterations || 100,
          body: edgeInfo.next, // The loop body step
        };
        if (edgeInfo.true) step.next = edgeInfo.true; // Exit step
        break;
    }

    return step;
  });

  return {
    name: metadata.name,
    description: metadata.description,
    steps,
    variables: {},
    tags: metadata.tags || [],
  };
}

/**
 * Convert backend workflow to React Flow nodes and edges
 */
export function workflowToFlow(workflow: BackendWorkflow): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // Calculate positions in a grid layout
  const GRID_X = 250;
  const GRID_Y = 150;
  let row = 0;
  let col = 0;

  for (const step of workflow.steps) {
    const node: Node = {
      id: step.id,
      type: step.type,
      position: { x: col * GRID_X + 100, y: row * GRID_Y + 100 },
      data: {
        label: step.name,
      },
    };

    // Set node-specific data
    switch (step.type) {
      case 'tool':
        node.data.tool = step.config.tool;
        node.data.config = step.config.parameters;
        break;

      case 'agent':
        node.data.agent = step.config.agent;
        node.data.prompt = step.config.prompt;
        break;

      case 'condition':
        node.data.condition = step.config.condition;
        break;

      case 'loop':
        node.data.iterateOver = step.config.iterateOver;
        node.data.maxIterations = step.config.maxIterations;
        break;
    }

    nodes.push(node);

    // Create edges based on next
    if (step.next) {
      if (typeof step.next === 'string') {
        edges.push({
          id: `e-${step.id}-${step.next}`,
          source: step.id,
          target: step.next,
          animated: true,
        });
      } else {
        // Condition node with true/false branches
        if (step.next.true) {
          edges.push({
            id: `e-${step.id}-true`,
            source: step.id,
            target: step.next.true,
            sourceHandle: 'true',
            animated: true,
          });
        }
        if (step.next.false) {
          edges.push({
            id: `e-${step.id}-false`,
            source: step.id,
            target: step.next.false,
            sourceHandle: 'false',
            animated: true,
          });
        }
      }
    }

    // Loop body edge
    if (step.type === 'loop' && step.config.body) {
      edges.push({
        id: `e-${step.id}-body`,
        source: step.id,
        target: step.config.body,
        sourceHandle: 'loop-body',
        animated: true,
      });
    }

    // Increment position
    col++;
    if (col > 2) {
      col = 0;
      row++;
    }
  }

  return { nodes, edges };
}

/**
 * Validate workflow structure
 */
export function validateWorkflow(nodes: Node[], edges: Edge[]): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Check for empty workflow
  if (nodes.length === 0) {
    errors.push('Workflow must have at least one node');
    return { valid: false, errors };
  }

  // Check for nodes without required configuration
  for (const node of nodes) {
    switch (node.type) {
      case 'tool':
        if (!node.data.tool) {
          errors.push(`Tool node "${node.data.label}" must have a tool selected`);
        }
        break;
      case 'agent':
        if (!node.data.agent) {
          errors.push(`Agent node "${node.data.label}" must have an agent selected`);
        }
        break;
      case 'condition':
        if (!node.data.condition) {
          errors.push(`Condition node "${node.data.label}" must have a condition defined`);
        }
        break;
      case 'loop':
        if (!node.data.iterateOver) {
          errors.push(`Loop node "${node.data.label}" must have an iteration target`);
        }
        break;
    }
  }

  // Check for disconnected nodes (nodes with no incoming or outgoing edges)
  const connectedNodes = new Set<string>();
  for (const edge of edges) {
    connectedNodes.add(edge.source);
    connectedNodes.add(edge.target);
  }

  // Allow single-node workflows
  if (nodes.length > 1) {
    for (const node of nodes) {
      if (!connectedNodes.has(node.id)) {
        errors.push(`Node "${node.data.label}" is disconnected from the workflow`);
      }
    }
  }

  // Check for circular dependencies (basic check)
  const visited = new Set<string>();
  const recursionStack = new Set<string>();

  function hasCycle(nodeId: string): boolean {
    if (recursionStack.has(nodeId)) return true;
    if (visited.has(nodeId)) return false;

    visited.add(nodeId);
    recursionStack.add(nodeId);

    const outgoingEdges = edges.filter((e) => e.source === nodeId);
    for (const edge of outgoingEdges) {
      // Skip loop-body edges for cycle detection (loops are allowed)
      if (edge.sourceHandle === 'loop-body') continue;
      if (hasCycle(edge.target)) return true;
    }

    recursionStack.delete(nodeId);
    return false;
  }

  for (const node of nodes) {
    if (hasCycle(node.id)) {
      errors.push('Workflow contains a circular dependency (excluding loops)');
      break;
    }
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Find the entry point of a workflow (node with no incoming edges)
 */
export function findEntryPoint(nodes: Node[], edges: Edge[]): Node | null {
  const nodesWithIncoming = new Set(edges.map((e) => e.target));
  const entryNodes = nodes.filter((n) => !nodesWithIncoming.has(n.id));
  return entryNodes[0] || null;
}

/**
 * Calculate execution order of nodes
 */
export function getExecutionOrder(nodes: Node[], edges: Edge[]): string[] {
  const order: string[] = [];
  const visited = new Set<string>();
  const adjacency = new Map<string, string[]>();

  // Build adjacency list
  for (const edge of edges) {
    if (!adjacency.has(edge.source)) {
      adjacency.set(edge.source, []);
    }
    adjacency.get(edge.source)!.push(edge.target);
  }

  // Find entry point
  const entry = findEntryPoint(nodes, edges);
  if (!entry) return nodes.map((n) => n.id);

  // BFS traversal
  const queue = [entry.id];
  while (queue.length > 0) {
    const nodeId = queue.shift()!;
    if (visited.has(nodeId)) continue;

    visited.add(nodeId);
    order.push(nodeId);

    const neighbors = adjacency.get(nodeId) || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        queue.push(neighbor);
      }
    }
  }

  return order;
}
