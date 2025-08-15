'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function SubscribePage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const check = async () => {
      try {
        const me = await apiClient.getCurrentUser();
        if (me.has_access) {
          router.replace('/dashboard');
          return;
        }
        setUsername(me.username);
      } catch {
        // Not logged in
      }
    };
    check();
  }, [router]);

  const startCheckout = async () => {
    setLoading(true);
    setError(null);
    try {
      const session = await apiClient.createCheckoutSession(username);
      if (session.url) {
        window.location.href = session.url;
      } else {
        setError('Failed to start checkout');
      }
    } catch (e: any) {
      setError(e.message || 'Failed to start checkout');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh] p-6">
      <div className="w-full max-w-lg space-y-4 bg-white/5 p-6 rounded-lg border border-white/10">
        <h1 className="text-2xl font-semibold">Subscribe</h1>
        <p className="opacity-80">Subscribe monthly to get full access. If you've been granted access manually, you can go to the dashboard.</p>
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <div className="flex gap-3">
          <button onClick={startCheckout} disabled={loading || !username} className="flex-1 py-2 rounded-md bg-purple-600 hover:bg-purple-500 disabled:opacity-50">{loading ? 'Redirecting…' : 'Subscribe with Stripe'}</button>
          <a href="/dashboard" className="px-4 py-2 rounded-md border border-white/10">Go to dashboard</a>
        </div>
        {!username && (
          <p className="text-sm opacity-70">Please <a href="/login" className="underline">log in</a> before subscribing.</p>
        )}
      </div>
    </div>
  );
}


