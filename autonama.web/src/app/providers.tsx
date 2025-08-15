'use client';

import { useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { useSignalsStore } from '@/store';

export function Providers({ children }: { children: React.ReactNode }) {
  const connectWebSocket = useSignalsStore(state => state.connectWebSocket);
  const disconnectWebSocket = useSignalsStore(state => state.disconnectWebSocket);

  useEffect(() => {
    // Connect WebSocket on app start
    connectWebSocket();

    // Cleanup on unmount
    return () => {
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket]);

  return (
    <>
      {children}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10B981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#EF4444',
              secondary: '#fff',
            },
          },
        }}
      />
    </>
  );
}
