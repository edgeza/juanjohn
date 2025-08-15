import type { Metadata } from 'next';
import './globals.css';
import { ThemeProvider } from '@/contexts/ThemeContext';
import ClientOnly from '@/components/ClientOnly';
import Navigation from '@/components/Navigation';

export const metadata: Metadata = {
  title: 'Autonama Research - Advanced Trading Platform',
  description: 'Elevate your trading with precision signals and advanced analytics',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body 
        className="transition-all duration-500"
        style={{ 
          backgroundColor: 'var(--bg-primary)',
          color: 'var(--text-primary)',
          minHeight: '100vh'
        }}
        suppressHydrationWarning={true}
      >
        <ClientOnly>
          <ThemeProvider>
            <div className="min-h-screen transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
              <Navigation />
              <main>
                {children}
              </main>
            </div>
          </ThemeProvider>
        </ClientOnly>
      </body>
    </html>
  );
}
