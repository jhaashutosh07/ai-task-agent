'use client';

import { useState } from 'react';
import { Volume2, VolumeX, Pause, Play } from 'lucide-react';
import { useSpeechSynthesis } from '@/hooks/useSpeechSynthesis';

interface VoiceOutputProps {
  text: string;
  autoPlay?: boolean;
  className?: string;
}

export default function VoiceOutput({ text, autoPlay = false, className = '' }: VoiceOutputProps) {
  const [hasPlayed, setHasPlayed] = useState(false);

  const { isSpeaking, isPaused, isSupported, speak, pause, resume, cancel } = useSpeechSynthesis({
    rate: 1,
    pitch: 1,
    onEnd: () => setHasPlayed(true),
  });

  const handleToggle = () => {
    if (isSpeaking) {
      if (isPaused) {
        resume();
      } else {
        pause();
      }
    } else {
      speak(text);
    }
  };

  const handleStop = () => {
    cancel();
  };

  if (!isSupported) {
    return null;
  }

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      <button
        onClick={handleToggle}
        className={`p-1.5 rounded transition-colors ${
          isSpeaking
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
        }`}
        title={isSpeaking ? (isPaused ? 'Resume' : 'Pause') : 'Read aloud'}
      >
        {isSpeaking ? (
          isPaused ? (
            <Play className="w-4 h-4" />
          ) : (
            <Pause className="w-4 h-4" />
          )
        ) : (
          <Volume2 className="w-4 h-4" />
        )}
      </button>

      {isSpeaking && (
        <button
          onClick={handleStop}
          className="p-1.5 rounded bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors"
          title="Stop"
        >
          <VolumeX className="w-4 h-4" />
        </button>
      )}

      {/* Speaking indicator */}
      {isSpeaking && !isPaused && (
        <div className="flex items-center gap-0.5 ml-1">
          <div className="w-1 h-3 bg-blue-400 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
          <div className="w-1 h-4 bg-blue-400 rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
          <div className="w-1 h-2 bg-blue-400 rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
        </div>
      )}
    </div>
  );
}
