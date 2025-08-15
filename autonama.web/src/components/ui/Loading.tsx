import { Loader2 } from 'lucide-react';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
}

export function Loading({ size = 'md', text, className = '' }: LoadingProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
  };

  return (
    <div className={`flex items-center justify-center gap-2 ${className}`}>
      <Loader2 className={`animate-spin ${sizeClasses[size]}`} />
      {text && <span className="text-sm text-gray-600">{text}</span>}
    </div>
  );
}

export function LoadingPage({ text = 'Loading...' }: { text?: string }) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <Loading size="lg" text={text} />
    </div>
  );
}

export function LoadingCard({ text = 'Loading...' }: { text?: string }) {
  return (
    <div className="rounded-lg bg-white p-8 shadow-sm">
      <Loading size="md" text={text} className="py-4" />
    </div>
  );
}
