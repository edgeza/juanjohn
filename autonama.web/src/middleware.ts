import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Define protected routes that require authentication
const protectedRoutes = [
  '/profile',
  '/settings',
  '/admin',
  '/analytics',
  '/alerts',
  '/assets',
  '/economic-calendar',
  '/news',
  '/tutorials',
  '/signals',
  '/optimization',
  '/billing',
  '/subscribe'
];

// Define auth routes
const authRoutes = ['/login', '/signup'];

export function middleware(request: NextRequest) {
  // Temporarily disabled - using client-side protection instead
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
