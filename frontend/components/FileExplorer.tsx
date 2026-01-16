'use client';

import { useState, useEffect } from 'react';
import { Folder, File, RefreshCw, ChevronRight } from 'lucide-react';
import { listFiles } from '@/lib/api';
import { useStore } from '@/lib/store';

export default function FileExplorer() {
  const { showFiles } = useStore();
  const [files, setFiles] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState('.');

  useEffect(() => {
    if (showFiles) {
      loadFiles();
    }
  }, [showFiles, currentPath]);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const result = await listFiles(currentPath);
      if (result.success) {
        setFiles(result.output);
      }
    } catch (err) {
      setFiles('Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  if (!showFiles) return null;

  return (
    <div className="w-72 bg-gray-800 border-l border-gray-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="font-medium text-white">Workspace Files</h3>
          <button
            onClick={loadFiles}
            disabled={loading}
            className="p-1 hover:bg-gray-700 rounded"
          >
            <RefreshCw
              className={`w-4 h-4 text-gray-400 ${loading ? 'animate-spin' : ''}`}
            />
          </button>
        </div>

        {/* Breadcrumb */}
        <div className="flex items-center gap-1 mt-2 text-sm text-gray-400">
          <button
            onClick={() => setCurrentPath('.')}
            className="hover:text-white"
          >
            workspace
          </button>
          {currentPath !== '.' && (
            <>
              <ChevronRight className="w-3 h-3" />
              <span>{currentPath}</span>
            </>
          )}
        </div>
      </div>

      {/* File list */}
      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="text-center text-gray-500 py-4">Loading...</div>
        ) : files ? (
          <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
            {files}
          </pre>
        ) : (
          <div className="text-center text-gray-500 py-4">
            <Folder className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No files yet</p>
            <p className="text-xs mt-1">Files created by the agent will appear here</p>
          </div>
        )}
      </div>
    </div>
  );
}
