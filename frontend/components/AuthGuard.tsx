'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Bot, Loader2 } from 'lucide-react';
import { getCurrentUser, isAuthenticated } from '@/lib/auth';
import { useStore } from '@/lib/store';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

export default function AuthGuard({ children, requireAuth = true }: AuthGuardProps) {
  const router = useRouter();
  const { user, setUser, isAuthLoading, setAuthLoading } = useStore();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      setAuthLoading(true);

      if (isAuthenticated()) {
        const currentUser = await getCurrentUser();
        if (currentUser) {
          setUser(currentUser);
        } else if (requireAuth) {
          router.push('/login');
        }
      } else if (requireAuth) {
        router.push('/login');
      }

      setAuthLoading(false);
      setChecked(true);
    };

    checkAuth();
  }, [requireAuth, router, setUser, setAuthLoading]);

  // Show loading while checking auth
  if (isAuthLoading || !checked) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4 animate-pulse">
            <Bot className="w-8 h-8 text-white" />
          </div>
          <div className="flex items-center justify-center gap-2 text-gray-400">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  // If auth required but no user, don't render (redirect will happen)
  if (requireAuth && !user) {
    return null;
  }

  return <>{children}</>;
}
