import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { Message, Settings, AgentEvent } from './types';

// User type (matching backend)
export interface User {
  id: string;
  email: string;
  username: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  usage_quota: number;
  usage_today: number;
  total_usage: number;
}

interface AppState {
  // Auth
  user: User | null;
  setUser: (user: User | null) => void;
  isAuthLoading: boolean;
  setAuthLoading: (loading: boolean) => void;

  // Messages
  messages: Message[];
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateLastMessage: (content: string, events?: AgentEvent[]) => void;
  clearMessages: () => void;

  // Loading state
  isLoading: boolean;
  setLoading: (loading: boolean) => void;

  // Current events
  currentEvents: AgentEvent[];
  addEvent: (event: AgentEvent) => void;
  clearEvents: () => void;

  // Settings
  settings: Settings | null;
  setSettings: (settings: Settings) => void;

  // UI state
  showSettings: boolean;
  toggleSettings: () => void;
  showFiles: boolean;
  toggleFiles: () => void;

  // Theme
  isDarkMode: boolean;
  toggleTheme: () => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // Auth
      user: null,
      setUser: (user) => set({ user }),
      isAuthLoading: true,
      setAuthLoading: (loading) => set({ isAuthLoading: loading }),

      // Messages
      messages: [],
      addMessage: (message) =>
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: crypto.randomUUID(),
              timestamp: new Date(),
            },
          ],
        })),
      updateLastMessage: (content, events) =>
        set((state) => {
          const messages = [...state.messages];
          if (messages.length > 0) {
            const lastIndex = messages.length - 1;
            messages[lastIndex] = {
              ...messages[lastIndex],
              content,
              events,
            };
          }
          return { messages };
        }),
      clearMessages: () => set({ messages: [] }),

      // Loading state
      isLoading: false,
      setLoading: (loading) => set({ isLoading: loading }),

      // Current events
      currentEvents: [],
      addEvent: (event) =>
        set((state) => ({
          currentEvents: [...state.currentEvents, event],
        })),
      clearEvents: () => set({ currentEvents: [] }),

      // Settings
      settings: null,
      setSettings: (settings) => set({ settings }),

      // UI state
      showSettings: false,
      toggleSettings: () => set((state) => ({ showSettings: !state.showSettings })),
      showFiles: false,
      toggleFiles: () => set((state) => ({ showFiles: !state.showFiles })),

      // Theme
      isDarkMode: true,
      toggleTheme: () =>
        set((state) => {
          const newDarkMode = !state.isDarkMode;
          if (typeof document !== 'undefined') {
            document.documentElement.classList.toggle('dark', newDarkMode);
          }
          return { isDarkMode: newDarkMode };
        }),
    }),
    {
      name: 'ai-agent-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        isDarkMode: state.isDarkMode,
        messages: state.messages.slice(-50), // Keep last 50 messages
      }),
    }
  )
);
