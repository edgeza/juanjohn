'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function BillingSuccessPage() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const sessionId = params.get('session_id');
    // Optionally, we could call backend to verify the session.
    const timer = setTimeout(() => router.replace('/dashboard'), 1500);
    return () => clearTimeout(timer);
  }, [params, router]);

  return (
    <div className="flex items-center justify-center min-h-[60vh] p-6">
      <div className="w-full max-w-lg space-y-4 bg-white/5 p-6 rounded-lg border border-white/10">
        <h1 className="text-2xl font-semibold">Payment successful</h1>
        <p className="opacity-80">Thanks! Redirecting to your dashboard…</p>
      </div>
    </div>
  );
}


