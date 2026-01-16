'use client';

import { useState, useEffect } from 'react';
import {
  Search, Globe, Code, FileText, Terminal, Database,
  Mail, Camera, FileCode, Zap, Play, ChevronDown, ChevronUp
} from 'lucide-react';
import { listTools, executeTool } from '@/lib/api';
import { Tool } from '@/lib/types';

const toolIcons: Record<string, React.ReactNode> = {
  web_search: <Search className="w-5 h-5" />,
  web_browser: <Globe className="w-5 h-5" />,
  code_executor: <Code className="w-5 h-5" />,
  file_manager: <FileText className="w-5 h-5" />,
  shell_execute: <Terminal className="w-5 h-5" />,
  database: <Database className="w-5 h-5" />,
  send_email: <Mail className="w-5 h-5" />,
  screenshot: <Camera className="w-5 h-5" />,
  pdf_reader: <FileCode className="w-5 h-5" />,
  api_caller: <Zap className="w-5 h-5" />
};

export default function ToolsExplorer() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTool, setExpandedTool] = useState<string | null>(null);
  const [toolParams, setToolParams] = useState<Record<string, any>>({});
  const [executing, setExecuting] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    setLoading(true);
    try {
      const res = await listTools();
      setTools(res.tools || []);
    } catch (err) {
      console.error('Failed to load tools:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (toolName: string) => {
    setExecuting(toolName);
    setResult(null);
    try {
      const params = toolParams[toolName] || {};
      const res = await executeTool(toolName, params);
      setResult(res);
    } catch (err) {
      setResult({ error: String(err) });
    } finally {
      setExecuting(null);
    }
  };

  const getRequiredParams = (tool: Tool): string[] => {
    return tool.parameters?.required || [];
  };

  const getParamProperties = (tool: Tool): Record<string, any> => {
    return tool.parameters?.properties || {};
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
        <h2 className="text-2xl font-bold text-white">Tools Explorer</h2>
        <span className="text-gray-400">{tools.length} tools available</span>
      </div>

      <div className="grid gap-4">
        {tools.map((tool) => (
          <div
            key={tool.name}
            className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden"
          >
            {/* Tool Header */}
            <div
              className="p-4 flex items-center justify-between cursor-pointer hover:bg-gray-700/50"
              onClick={() => setExpandedTool(expandedTool === tool.name ? null : tool.name)}
            >
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary-600/20 rounded-lg text-primary-400">
                  {toolIcons[tool.name] || <Zap className="w-5 h-5" />}
                </div>
                <div>
                  <div className="font-medium text-white">{tool.name}</div>
                  <div className="text-sm text-gray-400">{tool.description}</div>
                </div>
              </div>
              {expandedTool === tool.name ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </div>

            {/* Expanded Content */}
            {expandedTool === tool.name && (
              <div className="p-4 border-t border-gray-700 space-y-4">
                {/* Parameters */}
                <div>
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Parameters</h4>
                  <div className="space-y-3">
                    {Object.entries(getParamProperties(tool)).map(([key, schema]: [string, any]) => (
                      <div key={key}>
                        <label className="block text-sm text-gray-400 mb-1">
                          {key}
                          {getRequiredParams(tool).includes(key) && (
                            <span className="text-red-400 ml-1">*</span>
                          )}
                        </label>
                        {schema.type === 'boolean' ? (
                          <input
                            type="checkbox"
                            checked={toolParams[tool.name]?.[key] || false}
                            onChange={(e) => setToolParams({
                              ...toolParams,
                              [tool.name]: {
                                ...toolParams[tool.name],
                                [key]: e.target.checked
                              }
                            })}
                            className="w-4 h-4"
                          />
                        ) : schema.enum ? (
                          <select
                            value={toolParams[tool.name]?.[key] || ''}
                            onChange={(e) => setToolParams({
                              ...toolParams,
                              [tool.name]: {
                                ...toolParams[tool.name],
                                [key]: e.target.value
                              }
                            })}
                            className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white"
                          >
                            <option value="">Select...</option>
                            {schema.enum.map((opt: string) => (
                              <option key={opt} value={opt}>{opt}</option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type={schema.type === 'integer' ? 'number' : 'text'}
                            value={toolParams[tool.name]?.[key] || ''}
                            onChange={(e) => setToolParams({
                              ...toolParams,
                              [tool.name]: {
                                ...toolParams[tool.name],
                                [key]: e.target.value
                              }
                            })}
                            placeholder={schema.description}
                            className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-white"
                          />
                        )}
                        {schema.description && (
                          <p className="text-xs text-gray-500 mt-1">{schema.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Execute Button */}
                <button
                  onClick={() => handleExecute(tool.name)}
                  disabled={executing === tool.name}
                  className="w-full py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-lg flex items-center justify-center gap-2"
                >
                  {executing === tool.name ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  Execute
                </button>

                {/* Result */}
                {result && expandedTool === tool.name && (
                  <div className="mt-4 p-4 bg-gray-900 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-300 mb-2">Result</h4>
                    {result.error ? (
                      <div className="text-red-400 text-sm">{result.error}</div>
                    ) : (
                      <pre className="text-sm text-gray-300 whitespace-pre-wrap overflow-x-auto">
                        {result.output || JSON.stringify(result, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
