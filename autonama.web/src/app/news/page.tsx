'use client';

import { useState } from 'react';
import { Newspaper, Search, TrendingUp, TrendingDown, Minus, ArrowUp, ArrowRight, ArrowDown } from 'lucide-react';

export default function News() {
  const [searchQuery, setSearchQuery] = useState('');

  const topStories = [
    {
      id: 1,
      title: 'Market Volatility Expected Amidst Economic Uncertainty',
      description: 'Analysts predict increased market fluctuations as global economic indicators remain unclear. Investors are advised to exercise caution.',
      image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDGRXLjSq7czGE5-4YJU1hmehjJJWWPcaoMpZNvj-4Jzf8xXuDktSX1wM-m_Q_jw7y5EXGwIb9kB40X8CBU1HlDl0U2L-KmTGFkD6LUCm2LAxjV0k8say3uHZkUC_--ujtYJspBundPHI02GJv5VuTabwG3wBD4s0l0Yy5aJJvj3jSHdZOBUyEcL281nUdxbvHWWCXXdKtbY1DuIWkevk5d5rxxBf4F2elPUdi9LgQkGXCqJY1LAkdtbMRkwhhUuWTaHpj7PWbFONI',
      source: 'Financial Times',
      time: '2 hours ago'
    }
  ];

  const marketUpdates = [
    {
      id: 1,
      title: 'Tech Stocks Surge Despite Market Concerns',
      source: 'Financial Times',
      trend: 'up',
      time: '1 hour ago'
    },
    {
      id: 2,
      title: 'Oil Prices Rise on Supply Disruptions',
      source: 'Reuters',
      trend: 'up',
      time: '3 hours ago'
    },
    {
      id: 3,
      title: 'Central Bank Holds Interest Rates Steady',
      source: 'Bloomberg',
      trend: 'neutral',
      time: '4 hours ago'
    },
    {
      id: 4,
      title: 'Retail Sales Show Unexpected Growth',
      source: 'Wall Street Journal',
      trend: 'up',
      time: '5 hours ago'
    },
    {
      id: 5,
      title: 'Cryptocurrency Market Sees Mixed Signals',
      source: 'CNBC',
      trend: 'neutral',
      time: '6 hours ago'
    },
    {
      id: 6,
      title: 'Forex Market Reacts to Political Developments',
      source: 'MarketWatch',
      trend: 'down',
      time: '7 hours ago'
    }
  ];

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <ArrowUp className="h-5 w-5" style={{ color: '#44ff44' }} />;
      case 'down': return <ArrowDown className="h-5 w-5" style={{ color: '#ff4444' }} />;
      case 'neutral': return <ArrowRight className="h-5 w-5" style={{ color: '#666666' }} />;
      default: return <Minus className="h-5 w-5" style={{ color: '#666666' }} />;
    }
  };

  return (
    <div className="min-h-screen p-8 transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8 slide-in">
          <div className="flex items-center gap-4 mb-4">
            <div className="rounded-xl p-3 transition-colors duration-300" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
              <Newspaper className="h-8 w-8" style={{ color: 'var(--accent-color)' }} />
            </div>
            <div>
              <h1 className="text-3xl font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                News Feed
              </h1>
              <p className="mt-2 transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Stay informed with the latest market news and updates
              </p>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <div className="card glass-hover">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-3 rounded-l-xl" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                <Search className="h-5 w-5" style={{ color: 'var(--text-secondary)' }} />
              </div>
              <input
                type="text"
                placeholder="Search news..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 bg-transparent border-none outline-none text-base font-normal leading-normal transition-colors duration-300"
                style={{ color: 'var(--text-primary)' }}
              />
            </div>
          </div>
        </div>

        {/* Top Stories */}
        <div className="mb-8">
          <h2 className="text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            Top Stories
          </h2>
          <div className="p-4">
            {topStories.map((story) => (
              <div key={story.id} className="flex items-stretch justify-between gap-4 rounded-2xl p-6 glass-hover" style={{ backgroundColor: 'var(--glass-bg)' }}>
                <div className="flex flex-col gap-2 flex-[2_2_0px]">
                  <p className="text-base font-bold leading-tight transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                    {story.title}
                  </p>
                  <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                    {story.description}
                  </p>
                  <div className="flex items-center gap-4 mt-2">
                    <span className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                      Source: {story.source}
                    </span>
                    <span className="text-xs transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                      {story.time}
                    </span>
                  </div>
                </div>
                <div
                  className="w-full bg-center bg-no-repeat aspect-video bg-cover rounded-xl flex-1"
                  style={{ backgroundImage: `url("${story.image}")` }}
                ></div>
              </div>
            ))}
          </div>
        </div>

        {/* Market Updates */}
        <div className="mb-8">
          <h2 className="text-[22px] font-bold leading-tight tracking-[-0.015em] px-4 pb-3 pt-5 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            Market Updates
          </h2>
          <div className="space-y-2">
            {marketUpdates.map((update) => (
              <div key={update.id} className="flex items-center gap-4 p-4 rounded-2xl glass-hover" style={{ backgroundColor: 'var(--glass-bg)' }}>
                <div className="flex items-center justify-center rounded-xl p-3 shrink-0" style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                  {getTrendIcon(update.trend)}
                </div>
                <div className="flex flex-col justify-center flex-1">
                  <p className="text-base font-medium leading-normal line-clamp-1 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                    {update.title}
                  </p>
                  <div className="flex items-center gap-4 mt-1">
                    <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                      Source: {update.source}
                    </p>
                    <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                      {update.time}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* News Categories */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-6 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            News Categories
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="card float" style={{ animationDelay: '0.1s' }}>
              <h3 className="text-lg font-semibold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Economic News
              </h3>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                GDP, inflation, employment, and central bank updates
              </p>
            </div>

            <div className="card float" style={{ animationDelay: '0.2s' }}>
              <h3 className="text-lg font-semibold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Market Analysis
              </h3>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Technical analysis, market trends, and expert insights
              </p>
            </div>

            <div className="card float" style={{ animationDelay: '0.3s' }}>
              <h3 className="text-lg font-semibold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Company News
              </h3>
              <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Earnings reports, mergers, acquisitions, and corporate updates
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 