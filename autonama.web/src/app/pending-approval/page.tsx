'use client';

import Link from 'next/link';

export default function PendingApprovalPage() {
  return (
    <div className="flex items-center justify-center min-h-[60vh] p-6">
      <div className="w-full max-w-lg space-y-4 bg-white/5 p-6 rounded-lg border border-white/10">
        <h1 className="text-2xl font-semibold">Awaiting Access Approval</h1>
        <p className="opacity-80">Thanks for signing up. An admin will review and enable your access shortly. You can still browse public pages.</p>
        <div className="flex gap-3">
          <Link href="/" className="px-4 py-2 rounded-md border border-white/10">Home</Link>
          <Link href="/login" className="px-4 py-2 rounded-md bg-blue-600">Log in</Link>
        </div>
      </div>
    </div>
  );
}


