'use client';

import { useState } from 'react';
import { Calendar, Clock, TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function EconomicCalendar() {
  const [selectedDate, setSelectedDate] = useState(new Date());

  const events = [
    {
      id: 1,
      time: '09:30',
      currency: 'USD',
      event: 'Non-Farm Payrolls',
      impact: 'high',
      actual: '187K',
      forecast: '185K',
      previous: '173K',
      trend: 'up'
    },
    {
      id: 2,
      time: '10:00',
      currency: 'EUR',
      event: 'ECB Interest Rate Decision',
      impact: 'high',
      actual: '4.50%',
      forecast: '4.50%',
      previous: '4.25%',
      trend: 'neutral'
    },
    {
      id: 3,
      time: '11:00',
      currency: 'GBP',
      event: 'GDP Growth Rate',
      impact: 'medium',
      actual: '0.2%',
      forecast: '0.1%',
      previous: '0.0%',
      trend: 'up'
    },
    {
      id: 4,
      time: '12:30',
      currency: 'USD',
      event: 'ISM Manufacturing PMI',
      impact: 'medium',
      actual: '48.5',
      forecast: '49.0',
      previous: '49.8',
      trend: 'down'
    },
    {
      id: 5,
      time: '14:00',
      currency: 'JPY',
      event: 'Bank of Japan Policy Rate',
      impact: 'high',
      actual: '-0.10%',
      forecast: '-0.10%',
      previous: '-0.10%',
      trend: 'neutral'
    }
  ];

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return '#ff4444';
      case 'medium': return '#ffaa00';
      case 'low': return '#44ff44';
      default: return '#666666';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4" style={{ color: '#44ff44' }} />;
      case 'down': return <TrendingDown className="h-4 w-4" style={{ color: '#ff4444' }} />;
      case 'neutral': return <Minus className="h-4 w-4" style={{ color: '#666666' }} />;
      default: return <Minus className="h-4 w-4" style={{ color: '#666666' }} />;
    }
  };

  return (
    <div className="min-h-screen p-8 transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 slide-in">
          <div className="flex items-center gap-4 mb-4">
            <div className="rounded-xl p-3 transition-colors duration-300" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
              <Calendar className="h-8 w-8" style={{ color: 'var(--accent-color)' }} />
            </div>
            <div>
              <h1 className="text-3xl font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Economic Calendar
              </h1>
              <p className="mt-2 transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Track important market events and economic releases
              </p>
            </div>
          </div>
        </div>

        {/* Calendar Navigation */}
        <div className="mb-8">
          <div className="card glass-hover">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Today's Events
              </h2>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5" style={{ color: 'var(--text-secondary)' }} />
                <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                  {new Date().toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </span>
              </div>
            </div>

            {/* Events List */}
            <div className="space-y-4">
              {events.map((event) => (
                <div key={event.id} className="card float" style={{ backgroundColor: 'var(--glass-bg)' }}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: getImpactColor(event.impact) }}
                        ></div>
                        <span className="text-sm font-medium transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                          {event.time}
                        </span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-sm font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                          {event.currency} - {event.event}
                        </span>
                        <span className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                          Impact: {event.impact.toUpperCase()}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <span className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>Actual:</span>
                        <span className="text-sm font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                          {event.actual}
                        </span>
                        {getTrendIcon(event.trend)}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>Forecast:</span>
                        <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                          {event.forecast}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>Previous:</span>
                        <span className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                          {event.previous}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Upcoming Events */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-6 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            Upcoming Events
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="card float" style={{ animationDelay: '0.1s' }}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ff4444' }}></div>
                <span className="text-sm font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                  High Impact
                </span>
              </div>
              <h3 className="text-lg font-semibold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Federal Reserve Meeting
              </h3>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Tomorrow at 14:00 EST
              </p>
            </div>

            <div className="card float" style={{ animationDelay: '0.2s' }}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ffaa00' }}></div>
                <span className="text-sm font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                  Medium Impact
                </span>
              </div>
              <h3 className="text-lg font-semibold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Eurozone CPI
              </h3>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Tomorrow at 10:00 CET
              </p>
            </div>

            <div className="card float" style={{ animationDelay: '0.3s' }}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#44ff44' }}></div>
                <span className="text-sm font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                  Low Impact
                </span>
              </div>
              <h3 className="text-lg font-semibold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                UK Retail Sales
              </h3>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Tomorrow at 09:30 GMT
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 