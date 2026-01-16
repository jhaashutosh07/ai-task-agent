'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Trash2, Settings as SettingsIcon, FolderOpen, Loader2, Image, X } from 'lucide-react';
import { useStore } from '@/lib/store';
import { sendMessage, clearChat } from '@/lib/api';
import MessageBubble from './MessageBubble';
import TaskProgress from './TaskProgress';
import VoiceInput from './VoiceInput';
import VoiceOutput from './VoiceOutput';

export default function ChatInterface() {
  const [input, setInput] = useState('');
  const [images, setImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    messages,
    addMessage,
    clearMessages,
    isLoading,
    setLoading,
    currentEvents,
    addEvent,
    clearEvents,
    toggleSettings,
    toggleFiles,
  } = useStore();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentEvents]);

  // Handle image file selection
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter((file) => file.type.startsWith('image/'));

    if (validFiles.length > 0) {
      setImages((prev) => [...prev, ...validFiles].slice(0, 4)); // Max 4 images

      // Create previews
      validFiles.forEach((file) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          setImagePreviews((prev) => [...prev, e.target?.result as string].slice(0, 4));
        };
        reader.readAsDataURL(file);
      });
    }
  };

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
    setImagePreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const handleVoiceTranscript = (text: string) => {
    setInput((prev) => (prev ? `${prev} ${text}` : text));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setImages([]);
    setImagePreviews([]);
    clearEvents();

    // Add user message with images if any
    addMessage({
      role: 'user',
      content: userMessage,
      images: imagePreviews.length > 0 ? imagePreviews : undefined,
    });
    setLoading(true);

    try {
      // Send to backend (TODO: Add image support to API)
      const response = await sendMessage(userMessage);

      // Add events
      response.events.forEach((event) => addEvent(event));

      // Add assistant response
      addMessage({
        role: 'assistant',
        content: response.response,
        events: response.events,
      });
    } catch (error) {
      addMessage({
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Something went wrong'}`,
      });
    } finally {
      setLoading(false);
      clearEvents();
    }
  };

  const handleClear = async () => {
    try {
      await clearChat();
      clearMessages();
      clearEvents();
    } catch (error) {
      console.error('Failed to clear chat:', error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Handle drag and drop
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files).filter((file) =>
      file.type.startsWith('image/')
    );

    if (files.length > 0) {
      setImages((prev) => [...prev, ...files].slice(0, 4));
      files.forEach((file) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          setImagePreviews((prev) => [...prev, e.target?.result as string].slice(0, 4));
        };
        reader.readAsDataURL(file);
      });
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  return (
    <div
      className="flex flex-col h-full"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
        <div>
          <h1 className="text-xl font-semibold text-white">AI Task Agent</h1>
          <p className="text-sm text-gray-400">
            Your autonomous task automation assistant
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleFiles}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            title="Toggle file explorer"
          >
            <FolderOpen className="w-5 h-5 text-gray-400" />
          </button>
          <button
            onClick={toggleSettings}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            title="Settings"
          >
            <SettingsIcon className="w-5 h-5 text-gray-400" />
          </button>
          <button
            onClick={handleClear}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            title="Clear chat"
          >
            <Trash2 className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-blue-600/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Send className="w-8 h-8 text-blue-400" />
            </div>
            <h2 className="text-xl font-medium text-white mb-2">
              Welcome to AI Task Agent
            </h2>
            <p className="text-gray-400 max-w-md mx-auto">
              I can help you with complex tasks by searching the web, running code,
              and managing files. Try asking me to:
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {[
                'Search for Python tutorials',
                'Write a script to process data',
                'Create a file with some content',
                'Find the latest news on AI',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-full text-sm text-gray-300 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div key={message.id}>
                <MessageBubble message={message} />
                {message.role === 'assistant' && message.content && (
                  <div className="mt-1 ml-12">
                    <VoiceOutput text={message.content} />
                  </div>
                )}
              </div>
            ))}
          </>
        )}

        {/* Loading indicator with events */}
        {isLoading && (
          <div className="space-y-4">
            <TaskProgress events={currentEvents} />
            {currentEvents.length === 0 && (
              <div className="flex items-center gap-2 text-gray-400">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Thinking...</span>
              </div>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Image Previews */}
      {imagePreviews.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-700 flex gap-2 overflow-x-auto">
          {imagePreviews.map((preview, index) => (
            <div key={index} className="relative flex-shrink-0">
              <img
                src={preview}
                alt={`Upload ${index + 1}`}
                className="w-20 h-20 object-cover rounded-lg border border-gray-600"
              />
              <button
                onClick={() => removeImage(index)}
                className="absolute -top-2 -right-2 p-1 bg-red-600 rounded-full hover:bg-red-700 transition-colors"
              >
                <X className="w-3 h-3 text-white" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-700">
        <form onSubmit={handleSubmit} className="flex gap-3">
          {/* Image upload button */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleImageSelect}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-3 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors"
            title="Upload image"
          >
            <Image className="w-5 h-5 text-gray-400" />
          </button>

          {/* Voice input */}
          <VoiceInput
            onTranscript={handleVoiceTranscript}
            disabled={isLoading}
            className="p-3 rounded-xl"
          />

          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me to do something..."
            rows={1}
            className="flex-1 px-4 py-3 bg-gray-800 border border-gray-600 rounded-xl text-white placeholder-gray-500 resize-none focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2 text-center">
          Press Enter to send, Shift+Enter for new line. Drag & drop images or use the mic button.
        </p>
      </div>
    </div>
  );
}
