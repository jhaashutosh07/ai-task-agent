'use client';

import { Search, Globe, Code, FileText, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { AgentEvent } from '@/lib/types';

interface TaskProgressProps {
  events: AgentEvent[];
}

const toolIcons: Record<string, React.ReactNode> = {
  web_search: <Search className="w-4 h-4" />,
  web_browser: <Globe className="w-4 h-4" />,
  code_executor: <Code className="w-4 h-4" />,
  file_manager: <FileText className="w-4 h-4" />,
};

export default function TaskProgress({ events }: TaskProgressProps) {
  if (events.length === 0) return null;

  return (
    <div className="bg-gray-800/50 rounded-lg p-4 mb-4">
      <h3 className="text-sm font-medium text-gray-400 mb-3">Agent Activity</h3>
      <div className="space-y-2">
        {events.map((event, index) => (
          <EventItem key={index} event={event} />
        ))}
      </div>
    </div>
  );
}

function EventItem({ event }: { event: AgentEvent }) {
  if (event.type === 'thinking') {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-300">
        <Loader2 className="w-4 h-4 animate-spin text-primary-400" />
        <span>{event.data.message}</span>
      </div>
    );
  }

  if (event.type === 'tool_call') {
    const icon = event.data.tool ? toolIcons[event.data.tool] : null;
    return (
      <div className="flex items-center gap-2 text-sm">
        <div className="p-1 bg-primary-600/20 rounded text-primary-400">
          {icon || <Code className="w-4 h-4" />}
        </div>
        <span className="text-gray-300">
          Using <span className="font-medium text-primary-400">{event.data.tool}</span>
        </span>
        {event.data.args && (
          <span className="text-gray-500 text-xs truncate max-w-[200px]">
            {JSON.stringify(event.data.args).slice(0, 50)}...
          </span>
        )}
      </div>
    );
  }

  if (event.type === 'tool_result') {
    return (
      <div className="flex items-start gap-2 text-sm ml-6">
        {event.data.success ? (
          <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
        ) : (
          <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
        )}
        <span className={event.data.success ? 'text-gray-400' : 'text-red-400'}>
          {event.data.success
            ? event.data.output?.slice(0, 100) || 'Success'
            : event.data.error || 'Failed'}
          {event.data.output && event.data.output.length > 100 && '...'}
        </span>
      </div>
    );
  }

  if (event.type === 'error') {
    return (
      <div className="flex items-center gap-2 text-sm text-red-400">
        <XCircle className="w-4 h-4" />
        <span>{event.data.message}</span>
      </div>
    );
  }

  return null;
}
