'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Bot, Loader2 } from 'lucide-react';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to chat page
    router.replace('/chat');
  }, [router]);

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4 animate-pulse">
          <Bot className="w-8 h-8 text-white" />
        </div>
        <div className="flex items-center justify-center gap-2 text-gray-400">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Loading AI Task Agent...</span>
        </div>
      </div>
    </main>
  );
}
