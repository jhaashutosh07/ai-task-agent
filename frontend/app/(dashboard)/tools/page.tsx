'use client';

import { useState, useEffect } from 'react';
import {
  Search,
  Wrench,
  Play,
  Code,
  FileText,
  Globe,
  Terminal,
  Mail,
  Database,
  Camera,
  Loader2,
  ChevronDown,
  ChevronUp,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { listTools, executeTool } from '@/lib/api';

interface Tool {
  name: string;
  description: string;
  parameters: {
    type: string;
    properties: Record<string, { type: string; description: string }>;
    required?: string[];
  };
}

const toolIcons: Record<string, any> = {
  web_search: Globe,
  web_browser: Globe,
  code_executor: Code,
  file_manager: FileText,
  shell_execute: Terminal,
  send_email: Mail,
  database: Database,
  screenshot: Camera,
  api_caller: Globe,
  pdf_reader: FileText,
};

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [expandedTool, setExpandedTool] = useState<string | null>(null);
  const [executing, setExecuting] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, { success: boolean; output: string }>>({});
  const [params, setParams] = useState<Record<string, Record<string, string>>>({});

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      const data = await listTools();
      setTools(data.tools || []);
    } catch (error) {
      console.error('Failed to load tools:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (toolName: string) => {
    setExecuting(toolName);
    setResults((prev) => ({ ...prev, [toolName]: undefined } as any));

    try {
      const toolParams = params[toolName] || {};
      const result = await executeTool(toolName, toolParams);
      setResults((prev) => ({
        ...prev,
        [toolName]: { success: result.success, output: result.output || result.error },
      }));
    } catch (error: any) {
      setResults((prev) => ({
        ...prev,
        [toolName]: { success: false, output: error.message },
      }));
    } finally {
      setExecuting(null);
    }
  };

  const filteredTools = tools.filter(
    (tool) =>
      tool.name.toLowerCase().includes(search.toLowerCase()) ||
      tool.description.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Tools</h1>
        <p className="text-gray-400 mt-1">Explore and test available tools</p>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg py-2.5 pl-10 pr-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Search tools..."
        />
      </div>

      {/* Tools list */}
      <div className="space-y-3">
        {filteredTools.map((tool) => {
          const Icon = toolIcons[tool.name] || Wrench;
          const isExpanded = expandedTool === tool.name;
          const result = results[tool.name];
          const properties = tool.parameters?.properties || {};
          const required = tool.parameters?.required || [];

          return (
            <div
              key={tool.name}
              className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden"
            >
              {/* Tool header */}
              <div
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-700/50 transition-colors"
                onClick={() => setExpandedTool(isExpanded ? null : tool.name)}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-500/20 rounded-lg">
                    <Icon className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-white">{tool.name}</h3>
                    <p className="text-sm text-gray-400">{tool.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">
                    {Object.keys(properties).length} params
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </div>

              {/* Expanded content */}
              {isExpanded && (
                <div className="border-t border-gray-700 p-4 space-y-4">
                  {/* Parameters */}
                  {Object.keys(properties).length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-gray-300">Parameters</h4>
                      {Object.entries(properties).map(([name, prop]) => (
                        <div key={name}>
                          <label className="block text-sm text-gray-400 mb-1">
                            {name}
                            {required.includes(name) && (
                              <span className="text-red-400 ml-1">*</span>
                            )}
                            <span className="text-gray-500 ml-2 text-xs">({prop.type})</span>
                          </label>
                          <input
                            type="text"
                            value={params[tool.name]?.[name] || ''}
                            onChange={(e) =>
                              setParams((prev) => ({
                                ...prev,
                                [tool.name]: {
                                  ...prev[tool.name],
                                  [name]: e.target.value,
                                },
                              }))
                            }
                            className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder={prop.description}
                          />
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Execute button */}
                  <button
                    onClick={() => handleExecute(tool.name)}
                    disabled={executing === tool.name}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
                  >
                    {executing === tool.name ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                    Execute
                  </button>

                  {/* Result */}
                  {result && (
                    <div
                      className={`p-3 rounded-lg ${
                        result.success
                          ? 'bg-green-500/10 border border-green-500/30'
                          : 'bg-red-500/10 border border-red-500/30'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        {result.success ? (
                          <CheckCircle className="w-4 h-4 text-green-400" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-400" />
                        )}
                        <span
                          className={`text-sm font-medium ${
                            result.success ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          {result.success ? 'Success' : 'Error'}
                        </span>
                      </div>
                      <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap overflow-auto max-h-48">
                        {typeof result.output === 'object'
                          ? JSON.stringify(result.output, null, 2)
                          : result.output}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {filteredTools.length === 0 && (
          <div className="text-center py-12">
            <Wrench className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No tools found</p>
          </div>
        )}
      </div>
    </div>
  );
}
