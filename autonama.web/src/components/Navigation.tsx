'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname, useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import ThemeToggle from './ThemeToggle';
import { apiClient } from '@/lib/api';
import type { UserResponse } from '@/lib/api';

export default function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const navItems = [
    { href: '/dashboard', label: 'Dashboard' },
    ...(user ? [
      { href: '/analytics', label: 'Analytics' },
      { href: '/alerts', label: 'Alerts' },
      { href: '/assets', label: 'Assets' },
      { href: '/economic-calendar', label: 'Calendar' },
      { href: '/news', label: 'News' },
      { href: '/tutorials', label: 'Education' },
    ] : [])
  ];

  const publicNavItems = [
    { href: '/veriless', label: 'Project Veriless' }
  ];

  useEffect(() => {
    const checkAuth = async () => {
      try {
        console.log('[Navigation] Checking authentication...');
        const currentUser = await apiClient.getCurrentUser();
        console.log('[Navigation] User authenticated:', currentUser);
        setUser(currentUser);
        
        // If user is authenticated and on login/signup pages, redirect to dashboard
        if (currentUser && (pathname === '/login' || pathname === '/signup')) {
          router.push('/dashboard');
        }
      } catch (e) {
        console.log('[Navigation] Authentication failed:', e);
        setUser(null);
        // If we're on a protected route and not authenticated, redirect to dashboard
        if (typeof window !== 'undefined') {
          const protectedRoutes = ['/profile', '/settings', '/admin', '/analytics', '/alerts', '/assets', '/economic-calendar', '/news', '/tutorials', '/signals', '/optimization', '/billing', '/subscribe'];
          if (protectedRoutes.some(route => pathname.startsWith(route))) {
            router.push('/dashboard');
          }
        }
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [pathname, router]);

  // Add a separate effect to check auth when the component mounts or when user changes
  useEffect(() => {
    console.log('[Navigation] User state changed:', user);
  }, [user]);

  const handleLogout = async () => {
    try {
      await apiClient.logout();
      setUser(null);
      setIsProfileDropdownOpen(false);
      router.push('/login');
    } catch (e) {
      console.error('Logout failed:', e);
    }
  };

  const isAuthPage = pathname === '/login' || pathname === '/signup';

  if (isAuthPage) {
    return null; // Don't show navigation on auth pages
  }

  return (
    <header className="flex items-center justify-between whitespace-nowrap border-b px-10 py-4 transition-all duration-500 glass" style={{ borderColor: 'var(--glass-border)', backgroundColor: 'var(--glass-bg)' }}>
      <div className="flex items-center gap-4" style={{ color: 'var(--text-primary)' }}>
        <div className="flex items-center gap-3">
          <div className="relative w-8 h-8">
            <Image
              src="/logo.png"
              alt="Autonama Research Logo"
              width={32}
              height={32}
              className="object-contain"
              priority
            />
          </div>
          <h2 className="text-lg font-bold leading-tight tracking-tight text-glow">Autonama Research</h2>
        </div>
        
        {/* Project Veriless Link */}
        <div className="ml-8">
          {publicNavItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`text-sm font-medium leading-normal transition-all duration-300 ${
                pathname === item.href
                  ? 'nav-link-active'
                  : 'nav-link'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>

      <div className="flex flex-1 justify-end gap-8">
        {/* User Navigation Items */}
        {user && (
          <div className="flex items-center gap-9">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`text-sm font-medium leading-normal transition-all duration-300 ${
                  pathname === item.href
                    ? 'nav-link-active'
                    : 'nav-link'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>
        )}

        <div className="flex items-center gap-4">
          <ThemeToggle />
          
          {loading ? (
            <div className="w-8 h-8 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
          ) : user ? (
            <div className="relative">
              {/* Admin Link */}
              {user.is_admin && (
                <Link
                  href="/admin"
                  className="mr-4 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Admin
                </Link>
              )}

              {/* Profile Dropdown */}
              <button
                onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors"
              >
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <span className="text-sm font-medium">{user.username}</span>
                <svg className="w-4 h-4 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Profile Dropdown Menu */}
              {isProfileDropdownOpen && (
                <div className="absolute right-0 top-full mt-2 w-48 glass rounded-lg shadow-lg border border-white/10 z-50">
                  <div className="py-2">
                    <Link
                      href="/profile"
                      className="block px-4 py-2 text-sm hover:bg-white/5 transition-colors"
                      onClick={() => setIsProfileDropdownOpen(false)}
                    >
                      Profile
                    </Link>
                    <Link
                      href="/settings"
                      className="block px-4 py-2 text-sm hover:bg-white/5 transition-colors"
                      onClick={() => setIsProfileDropdownOpen(false)}
                    >
                      Settings
                    </Link>
                    <div className="border-t border-white/10 my-1"></div>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-white/5 transition-colors"
                    >
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex gap-2">
              <Link href="/signup">
                <button className="btn-secondary">
                  <span className="truncate">Get Started</span>
                </button>
              </Link>
              <Link href="/login">
                <button className="btn-primary" onClick={() => router.push('/login')}>
                  <span className="truncate">Log In</span>
                </button>
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Mobile menu button */}
      <button
        className="md:hidden transition-all duration-300"
        style={{ color: 'var(--text-primary)' }}
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Mobile menu */}
      {isMobileMenuOpen && (
        <div className="absolute top-full left-0 right-0 border-b transition-all duration-500 md:hidden glass" style={{ backgroundColor: 'var(--glass-bg)', borderColor: 'var(--glass-border)' }}>
          <div className="flex flex-col p-6 space-y-4">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`text-sm font-medium leading-normal transition-all duration-300 ${
                  pathname === item.href
                    ? 'nav-link-active'
                    : 'nav-link'
                }`}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {item.label}
              </Link>
            ))}
            
            {/* Mobile auth section */}
            {user ? (
              <>
                {user.is_admin && (
                  <Link
                    href="/admin"
                    className="text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    Admin Panel
                  </Link>
                )}
                <Link
                  href="/profile"
                  className="text-sm font-medium leading-normal transition-all duration-300"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Profile
                </Link>
                <button
                  onClick={() => {
                    handleLogout();
                    setIsMobileMenuOpen(false);
                  }}
                  className="text-sm font-medium text-red-400 hover:text-red-300 transition-colors text-left"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/signup"
                  className="text-sm font-medium leading-normal transition-all duration-300"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Get Started
                </Link>
                <Link
                  href="/login"
                  className="text-sm font-medium leading-normal transition-all duration-300"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Log In
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
