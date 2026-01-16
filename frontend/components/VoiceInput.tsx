'use client';

import { useState, useEffect } from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { useSpeechRecognition } from '@/hooks/useSpeechRecognition';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
  className?: string;
}

export default function VoiceInput({ onTranscript, disabled = false, className = '' }: VoiceInputProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const {
    isListening,
    transcript,
    interimTranscript,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechRecognition({
    continuous: true,
    interimResults: true,
    onResult: (text, isFinal) => {
      if (isFinal) {
        onTranscript(text);
      }
    },
  });

  const handleToggle = () => {
    if (isListening) {
      stopListening();
      if (transcript) {
        onTranscript(transcript);
      }
      resetTranscript();
    } else {
      startListening();
    }
  };

  if (!isSupported) {
    return (
      <button
        disabled
        className={`p-2 rounded-lg bg-gray-700 text-gray-500 cursor-not-allowed ${className}`}
        title="Voice input not supported in this browser"
      >
        <MicOff className="w-5 h-5" />
      </button>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={handleToggle}
        disabled={disabled}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className={`p-2 rounded-lg transition-all ${
          isListening
            ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
            : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
      >
        {isListening ? (
          <Mic className="w-5 h-5" />
        ) : (
          <Mic className="w-5 h-5" />
        )}
      </button>

      {/* Recording indicator */}
      {isListening && (
        <div className="absolute -top-1 -right-1 w-3 h-3">
          <span className="absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75 animate-ping" />
          <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
        </div>
      )}

      {/* Tooltip */}
      {showTooltip && !isListening && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-700 text-white text-xs rounded whitespace-nowrap">
          Click to speak
        </div>
      )}

      {/* Interim transcript display */}
      {isListening && interimTranscript && (
        <div className="absolute top-full left-0 mt-2 p-2 bg-gray-800 border border-gray-700 rounded-lg shadow-lg min-w-[200px] max-w-[300px] z-10">
          <div className="flex items-center gap-2 mb-1">
            <Loader2 className="w-3 h-3 animate-spin text-blue-400" />
            <span className="text-xs text-gray-400">Listening...</span>
          </div>
          <p className="text-sm text-white">{interimTranscript}</p>
        </div>
      )}
    </div>
  );
}
