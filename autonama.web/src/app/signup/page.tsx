'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { useRouter } from 'next/navigation';

// Animated background component
const AnimatedBackground = () => {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-black via-gray-900 to-black animate-gradient-shift"></div>
      
      {/* Floating particles */}
      <div className="absolute inset-0">
        {[...Array(50)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-white/20 rounded-full animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 20}s`,
              animationDuration: `${10 + Math.random() * 20}s`
            }}
          />
        ))}
      </div>
      
      {/* Animated circles */}
      <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-white/5 rounded-full blur-3xl animate-pulse"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-gray-500/5 rounded-full blur-3xl animate-pulse" style={{animationDelay: '2s'}}></div>
      <div className="absolute top-1/2 left-1/2 w-48 h-48 bg-white/5 rounded-full blur-3xl animate-pulse" style={{animationDelay: '4s'}}></div>
      
      {/* Grid pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:50px_50px] animate-grid-move"></div>
    </div>
  );
};

// Floating card component
const FloatingCard = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="relative group">
      {/* Glow effect */}
      <div className="absolute -inset-1 bg-gradient-to-r from-white/20 via-gray-500/20 to-white/20 rounded-2xl blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200 animate-tilt"></div>
      
      {/* Main card */}
      <div className="relative bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 shadow-2xl p-8 transform transition-all duration-300 hover:scale-105 hover:shadow-3xl">
        {/* Inner glow */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-2xl"></div>
        
        {/* Content */}
        <div className="relative z-10">
          {children}
        </div>
      </div>
    </div>
  );
};

export default function SignupPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await apiClient.register({ username, email, password });
      router.push('/pending-approval');
    } catch (err: any) {
      setError(err.message || 'Signup failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden">
      <AnimatedBackground />
      
      <div className="relative z-10 w-full max-w-md">
        <FloatingCard>
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-white to-gray-300 rounded-2xl flex items-center justify-center shadow-lg">
              <img 
                src="/autonama_research_logo.png" 
                alt="Autonama Logo" 
                className="w-10 h-10 object-contain"
              />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              Join Us
            </h1>
            <p className="text-white/60 mt-2">Create your account</p>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-xl backdrop-blur-sm">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-red-300 text-sm">{error}</span>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={onSubmit} className="space-y-6">
            {/* Username field */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-white/80">
                Username
              </label>
              <div className="relative">
                <div                 className={`absolute inset-0 rounded-xl transition-all duration-300 ${
                  focusedField === 'username' 
                    ? 'bg-gradient-to-r from-white/20 to-gray-500/20' 
                    : 'bg-white/5'
                }`}></div>
                <input
                  className="relative w-full px-4 py-3 bg-transparent border border-white/20 rounded-xl outline-none text-white placeholder-white/50 transition-all duration-300 focus:border-white/50 focus:ring-2 focus:ring-white/20"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => setFocusedField('username')}
                  onBlur={() => setFocusedField(null)}
                  placeholder="Choose a username"
                  required
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <svg className="w-5 h-5 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Email field */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-white/80">
                Email
              </label>
              <div className="relative">
                <div className={`absolute inset-0 rounded-xl transition-all duration-300 ${
                  focusedField === 'email' 
                    ? 'bg-gradient-to-r from-white/20 to-gray-500/20' 
                    : 'bg-white/5'
                }`}></div>
                <input
                  type="email"
                  className="relative w-full px-4 py-3 bg-transparent border border-white/20 rounded-xl outline-none text-white placeholder-white/50 transition-all duration-300 focus:border-white/50 focus:ring-2 focus:ring-white/20"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onFocus={() => setFocusedField('email')}
                  onBlur={() => setFocusedField(null)}
                  placeholder="Enter your email"
                  required
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <svg className="w-5 h-5 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Password field */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-white/80">
                Password
              </label>
              <div className="relative">
                <div className={`absolute inset-0 rounded-xl transition-all duration-300 ${
                  focusedField === 'password' 
                    ? 'bg-gradient-to-r from-white/20 to-gray-500/20' 
                    : 'bg-white/5'
                }`}></div>
                <input
                  type="password"
                  className="relative w-full px-4 py-3 bg-transparent border border-white/20 rounded-xl outline-none text-white placeholder-white/50 transition-all duration-300 focus:border-white/50 focus:ring-2 focus:ring-white/20"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => setFocusedField('password')}
                  onBlur={() => setFocusedField(null)}
                  placeholder="Create a password"
                  required
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <svg className="w-5 h-5 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Submit button */}
            <button
              disabled={isLoading}
              className="w-full py-3 px-6 bg-gradient-to-r from-white to-gray-300 hover:from-gray-200 hover:to-white disabled:from-gray-600 disabled:to-gray-600 text-black font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 hover:shadow-lg disabled:transform-none disabled:cursor-not-allowed relative overflow-hidden group"
            >
              {/* Button background animation */}
              <div className="absolute inset-0 bg-gradient-to-r from-gray-100 to-white opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              
              {/* Button content */}
              <span className="relative flex items-center justify-center space-x-2">
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>Creating account...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    <span>Create Account</span>
                  </>
                )}
              </span>
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-white/60 text-sm">
              Already have an account?{' '}
              <a 
                href="/login" 
                className="text-white hover:text-gray-300 font-medium transition-colors duration-200 underline decoration-white/30 underline-offset-4 hover:decoration-gray-300/50"
              >
                Sign in
              </a>
            </p>
          </div>
        </FloatingCard>
      </div>
    </div>
  );
}


