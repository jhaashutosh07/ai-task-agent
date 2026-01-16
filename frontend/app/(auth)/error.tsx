'use client';

import { useEffect } from 'react';
import Link from 'next/link';

export default function AuthError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Auth error:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="text-center p-8 max-w-md">
        <div className="text-5xl mb-4">🔐</div>
        <h2 className="text-xl font-bold text-white mb-4">Authentication Error</h2>
        <p className="text-gray-400 mb-6 text-sm">
          {error.message || 'An error occurred during authentication'}
        </p>
        <div className="space-x-4">
          <button
            onClick={reset}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            Try again
          </button>
          <Link
            href="/login"
            className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors text-sm inline-block"
          >
            Back to Login
          </Link>
        </div>
      </div>
    </div>
  );
}
