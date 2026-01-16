'use client';

import { useState } from 'react';
import { Search, FileText, Bot, Globe, Code, Mail, Database, X } from 'lucide-react';

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: any;
  nodes: any[];
  edges: any[];
}

const templates: WorkflowTemplate[] = [
  {
    id: 'web-research',
    name: 'Web Research Pipeline',
    description: 'Search the web, extract content, and summarize findings',
    category: 'Research',
    icon: Globe,
    nodes: [
      {
        id: 'search',
        type: 'tool',
        position: { x: 100, y: 100 },
        data: { label: 'Web Search', tool: 'web_search', description: 'Search for relevant information' },
      },
      {
        id: 'extract',
        type: 'tool',
        position: { x: 100, y: 250 },
        data: { label: 'Extract Content', tool: 'web_browser', description: 'Extract content from search results' },
      },
      {
        id: 'summarize',
        type: 'agent',
        position: { x: 100, y: 400 },
        data: { label: 'Summarize', agent: 'analyst', prompt: 'Summarize the extracted content' },
      },
    ],
    edges: [
      { id: 'e1-2', source: 'search', target: 'extract', animated: true },
      { id: 'e2-3', source: 'extract', target: 'summarize', animated: true },
    ],
  },
  {
    id: 'code-review',
    name: 'Code Review Workflow',
    description: 'Analyze code, identify issues, and suggest improvements',
    category: 'Development',
    icon: Code,
    nodes: [
      {
        id: 'read-code',
        type: 'tool',
        position: { x: 100, y: 100 },
        data: { label: 'Read Code', tool: 'file_manager', description: 'Read source code files' },
      },
      {
        id: 'analyze',
        type: 'agent',
        position: { x: 100, y: 250 },
        data: { label: 'Analyze Code', agent: 'coder', prompt: 'Analyze the code for issues and improvements' },
      },
      {
        id: 'check-quality',
        type: 'condition',
        position: { x: 100, y: 400 },
        data: { label: 'Quality Check', condition: 'result.issues.length === 0' },
      },
      {
        id: 'report-issues',
        type: 'agent',
        position: { x: 250, y: 550 },
        data: { label: 'Report Issues', agent: 'analyst', prompt: 'Generate a detailed report of issues found' },
      },
    ],
    edges: [
      { id: 'e1-2', source: 'read-code', target: 'analyze', animated: true },
      { id: 'e2-3', source: 'analyze', target: 'check-quality', animated: true },
      { id: 'e3-4', source: 'check-quality', target: 'report-issues', sourceHandle: 'false', animated: true },
    ],
  },
  {
    id: 'data-processing',
    name: 'Data Processing Pipeline',
    description: 'Process data files, analyze, and generate reports',
    category: 'Data',
    icon: Database,
    nodes: [
      {
        id: 'load-data',
        type: 'tool',
        position: { x: 100, y: 100 },
        data: { label: 'Load Data', tool: 'file_manager', description: 'Load data from files' },
      },
      {
        id: 'process-loop',
        type: 'loop',
        position: { x: 100, y: 250 },
        data: { label: 'Process Items', iterateOver: 'context.data', maxIterations: 100 },
      },
      {
        id: 'analyze-item',
        type: 'agent',
        position: { x: 300, y: 250 },
        data: { label: 'Analyze Item', agent: 'analyst', prompt: 'Analyze the current data item' },
      },
      {
        id: 'generate-report',
        type: 'agent',
        position: { x: 100, y: 400 },
        data: { label: 'Generate Report', agent: 'analyst', prompt: 'Generate a summary report of all processed data' },
      },
    ],
    edges: [
      { id: 'e1-2', source: 'load-data', target: 'process-loop', animated: true },
      { id: 'e2-3', source: 'process-loop', target: 'analyze-item', sourceHandle: 'loop-body', animated: true },
      { id: 'e3-2', source: 'analyze-item', target: 'process-loop', animated: true },
      { id: 'e2-4', source: 'process-loop', target: 'generate-report', sourceHandle: 'exit', animated: true },
    ],
  },
  {
    id: 'email-automation',
    name: 'Email Automation',
    description: 'Generate and send automated email responses',
    category: 'Automation',
    icon: Mail,
    nodes: [
      {
        id: 'draft-email',
        type: 'agent',
        position: { x: 100, y: 100 },
        data: { label: 'Draft Email', agent: 'executor', prompt: 'Draft an email response based on the input' },
      },
      {
        id: 'review',
        type: 'condition',
        position: { x: 100, y: 250 },
        data: { label: 'Review Required?', condition: 'context.requiresReview === true' },
      },
      {
        id: 'send-email',
        type: 'tool',
        position: { x: 250, y: 400 },
        data: { label: 'Send Email', tool: 'send_email', description: 'Send the drafted email' },
      },
    ],
    edges: [
      { id: 'e1-2', source: 'draft-email', target: 'review', animated: true },
      { id: 'e2-3', source: 'review', target: 'send-email', sourceHandle: 'false', animated: true },
    ],
  },
];

interface TemplateGalleryProps {
  onSelect: (template: WorkflowTemplate) => void;
  onClose: () => void;
}

export default function TemplateGallery({ onSelect, onClose }: TemplateGalleryProps) {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const categories = [...new Set(templates.map((t) => t.category))];

  const filteredTemplates = templates.filter((t) => {
    const matchesSearch =
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = !selectedCategory || t.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl shadow-2xl border border-gray-700 w-full max-w-3xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Workflow Templates</h2>
            <p className="text-sm text-gray-400">Start with a pre-built workflow template</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search and filters */}
        <div className="p-4 border-b border-gray-700 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg py-2 pl-10 pr-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Search templates..."
            />
          </div>

          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`px-3 py-1 rounded-full text-sm transition-colors ${
                !selectedCategory
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              All
            </button>
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  selectedCategory === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {/* Templates grid */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredTemplates.map((template) => {
              const Icon = template.icon;
              return (
                <div
                  key={template.id}
                  onClick={() => onSelect(template)}
                  className="bg-gray-700/50 border border-gray-600 rounded-xl p-4 cursor-pointer hover:border-blue-500 hover:bg-gray-700 transition-all group"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-blue-500/20 rounded-lg group-hover:bg-blue-500/30 transition-colors">
                      <Icon className="w-6 h-6 text-blue-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-white group-hover:text-blue-400 transition-colors">
                        {template.name}
                      </h3>
                      <p className="text-sm text-gray-400 mt-1">{template.description}</p>
                      <div className="flex items-center gap-2 mt-3">
                        <span className="px-2 py-0.5 bg-gray-600 rounded text-xs text-gray-300">
                          {template.category}
                        </span>
                        <span className="text-xs text-gray-500">
                          {template.nodes.length} nodes
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {filteredTemplates.length === 0 && (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400">No templates found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
