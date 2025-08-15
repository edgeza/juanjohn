'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, BarChart3, Settings, ArrowRight, Calendar, Newspaper, GraduationCap, Bell, Activity, Target, Zap } from 'lucide-react';
import Link from 'next/link';
import { useTheme } from '@/contexts/ThemeContext';

// Preloader Component
function Preloader() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="relative">
        <div className="w-16 h-16 border-4 border-gray-200 rounded-full animate-spin" style={{ borderTopColor: 'var(--accent-color)' }}></div>
        <div className="mt-4 text-center">
          <div className="text-lg font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            Autonama Research
          </div>
          <div className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
            Loading Dashboard...
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate loading time
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return <Preloader />;
  }

  return (
    <div className="min-h-screen transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="mx-auto max-w-7xl pt-8">
        {/* Hero Banner */}
        <div className="relative overflow-hidden rounded-3xl mb-8 slide-in">
          <div 
            className="relative z-10 p-12 md:p-16 text-center"
            style={{
              background: isDark 
                ? 'linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.6) 100%)'
                : 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)'
            }}
          >
            <div className="max-w-4xl mx-auto">
              <h1 className="text-4xl md:text-6xl font-bold mb-6 text-glow" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                Autonama Research Dashboard
              </h1>
              <p className="text-xl md:text-2xl mb-8 leading-relaxed" style={{ color: isDark ? '#e0e0e0' : '#333333' }}>
                Advanced trading optimization and analytics platform
              </p>
              
              {/* Feature Highlights */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="flex items-center justify-center gap-3 p-4 rounded-2xl glass" style={{ 
                  backgroundColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)', 
                  border: isDark ? '1px solid rgba(255, 255, 255, 0.2)' : '1px solid rgba(0, 0, 0, 0.2)' 
                }}>
                  <Target className="h-6 w-6" style={{ color: isDark ? '#ffffff' : '#000000' }} />
                  <span className="font-semibold" style={{ color: isDark ? '#ffffff' : '#000000' }}>Precision Alerts</span>
                </div>
                <div className="flex items-center justify-center gap-3 p-4 rounded-2xl glass" style={{ 
                  backgroundColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)', 
                  border: isDark ? '1px solid rgba(255, 255, 255, 0.2)' : '1px solid rgba(0, 0, 0, 0.2)' 
                }}>
                  <Activity className="h-6 w-6" style={{ color: isDark ? '#ffffff' : '#000000' }} />
                  <span className="font-semibold" style={{ color: isDark ? '#ffffff' : '#000000' }}>Real-time Data</span>
                </div>
                <div className="flex items-center justify-center gap-3 p-4 rounded-2xl glass" style={{ 
                  backgroundColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)', 
                  border: isDark ? '1px solid rgba(255, 255, 255, 0.2)' : '1px solid rgba(0, 0, 0, 0.2)' 
                }}>
                  <Zap className="h-6 w-6" style={{ color: isDark ? '#ffffff' : '#000000' }} />
                  <span className="font-semibold" style={{ color: isDark ? '#ffffff' : '#000000' }}>Smart Analytics</span>
                </div>
              </div>
              
              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/alerts">
                  <button className="btn-primary text-lg px-8 py-4 pulse-glow">
                    <Bell className="h-5 w-5" />
                    <span>View Alerts</span>
                  </button>
                </Link>
                <Link href="/assets">
                  <button className="btn-secondary text-lg px-8 py-4">
                    <BarChart3 className="h-5 w-5" />
                    <span>Explore Assets</span>
                  </button>
                </Link>
              </div>
            </div>
          </div>
          
          {/* Background Image with Theme Adaptation */}
          <div 
            className="absolute inset-0 z-0"
            style={{
              backgroundImage: 'url("https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80")',
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              backgroundRepeat: 'no-repeat',
              filter: isDark ? 'brightness(0.7) contrast(1.1)' : 'brightness(0.9) contrast(1.2)',
              transition: 'all 0.5s ease'
            }}
          />
          
          {/* Theme-aware overlay */}
          <div 
            className="absolute inset-0 z-0"
            style={{
              background: isDark ? '#000000' : '#ffffff',
              opacity: isDark ? 0.3 : 0.4,
              transition: 'all 0.5s ease'
            }}
          />
        </div>

        {/* Quick Access Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Link href="/economic-calendar" className="group">
            <div className="card transition-all hover:scale-[1.02] glass-hover float" style={{ animationDelay: '0.1s' }}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <div className="rounded-xl p-3 transition-colors duration-300" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                      <Calendar className="h-6 w-6" style={{ color: 'var(--accent-color)' }} />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Economic Calendar</h3>
                      <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>Track market events and releases</p>
                    </div>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" style={{ color: 'var(--text-secondary)' }} />
              </div>
            </div>
          </Link>

          <Link href="/news" className="group">
            <div className="card transition-all hover:scale-[1.02] glass-hover float" style={{ animationDelay: '0.2s' }}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <div className="rounded-xl p-3 transition-colors duration-300" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                      <Newspaper className="h-6 w-6" style={{ color: 'var(--accent-color)' }} />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>News Feed</h3>
                      <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>Latest market news and updates</p>
                    </div>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" style={{ color: 'var(--text-secondary)' }} />
              </div>
            </div>
          </Link>

          <Link href="/tutorials" className="group">
            <div className="card transition-all hover:scale-[1.02] glass-hover float" style={{ animationDelay: '0.3s' }}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <div className="rounded-xl p-3 transition-colors duration-300" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                      <GraduationCap className="h-6 w-6" style={{ color: 'var(--accent-color)' }} />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Education</h3>
                      <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>Tutorials and learning resources</p>
                    </div>
                  </div>
                </div>
                <ArrowRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" style={{ color: 'var(--text-secondary)' }} />
              </div>
            </div>
          </Link>

          <div className="card glass-hover float" style={{ animationDelay: '0.4s' }}>
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <div className="rounded-xl p-3 transition-colors duration-300" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                    <BarChart3 className="h-6 w-6" style={{ color: 'var(--accent-color)' }} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Analytics</h3>
                    <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>Advanced market analysis</p>
                  </div>
                </div>
              </div>
              <span className="rounded-full px-3 py-1 text-xs font-medium transition-all duration-300 glass" style={{ backgroundColor: 'var(--glass-bg)', color: 'var(--text-primary)', border: '1px solid var(--glass-border)' }}>
                Coming Soon
              </span>
            </div>
          </div>
        </div>

        {/* Market Overview */}
        <div className="card glass-hover">
          <h2 className="text-2xl font-bold mb-6 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            Market Overview
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-6 rounded-2xl glass" style={{ backgroundColor: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
              <TrendingUp className="h-8 w-8 mx-auto mb-3" style={{ color: 'var(--accent-color)' }} />
              <h3 className="text-lg font-semibold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Active Alerts</h3>
              <p className="text-3xl font-bold text-green-500">24</p>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>Real-time signals</p>
            </div>
            
            <div className="text-center p-6 rounded-2xl glass" style={{ backgroundColor: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
              <BarChart3 className="h-8 w-8 mx-auto mb-3" style={{ color: 'var(--accent-color)' }} />
              <h3 className="text-lg font-semibold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Tracked Assets</h3>
              <p className="text-3xl font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>100+</p>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>Top volume pairs</p>
            </div>
            
            <div className="text-center p-6 rounded-2xl glass" style={{ backgroundColor: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}>
              <Activity className="h-8 w-8 mx-auto mb-3" style={{ color: 'var(--accent-color)' }} />
              <h3 className="text-lg font-semibold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>System Status</h3>
              <p className="text-3xl font-bold text-green-500">Online</p>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>All systems operational</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 