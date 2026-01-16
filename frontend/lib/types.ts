export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  events?: AgentEvent[];
  images?: string[];
}

export interface AgentEvent {
  type: string;
  agent?: string;
  data: {
    message?: string;
    tool?: string;
    args?: Record<string, any>;
    success?: boolean;
    output?: string;
    error?: string;
    task_id?: string;
    description?: string;
  };
}

export interface ChatResponse {
  response: string;
  events: AgentEvent[];
  execution_time: number;
}

export interface Settings {
  llm_provider: 'openai' | 'ollama';
  openai_model: string;
  ollama_model: string;
  openai_configured: boolean;
  ollama_available: boolean;
  tools_count: number;
  agents_count: number;
}

export interface Tool {
  name: string;
  description: string;
  parameters: Record<string, any>;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  variables: Record<string, any>;
  tags: string[];
  version?: string;
  updated_at?: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  type: 'tool' | 'agent' | 'condition' | 'loop' | 'parallel' | 'wait' | 'transform';
  config: Record<string, any>;
  inputs?: Record<string, string>;
  condition?: string;
  on_error?: string;
}

export interface ScheduledTask {
  id: string;
  workflow_id: string;
  name: string;
  enabled: boolean;
  last_run?: string;
  next_run?: string;
  run_count: number;
}

export interface MemoryItem {
  id: string;
  content: string;
  relevance: number;
  metadata: Record<string, any>;
}

export interface KnowledgeEntry {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
}
