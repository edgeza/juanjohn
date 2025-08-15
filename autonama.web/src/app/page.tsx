'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
      <div className="px-40 flex flex-1 justify-center py-5">
        <div className="layout-content-container flex flex-col max-w-[960px] flex-1">
          <div className="@container">
            <div className="@[480px]:p-4">
              <div
                className="flex min-h-[480px] flex-col gap-6 bg-cover bg-center bg-no-repeat @[480px]:gap-8 @[480px]:rounded-2xl items-center justify-center p-8 glass-hover"
                style={{
                  backgroundImage: 'linear-gradient(rgba(0, 0, 0, 0.3) 0%, rgba(0, 0, 0, 0.6) 100%), url("https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80")'
                }}
              >
                <div className="flex flex-col gap-4 text-center slide-in">
                  <h1 className="text-white text-4xl font-black leading-tight tracking-tighter @[480px]:text-5xl @[480px]:font-black @[480px]:leading-tight @[480px]:tracking-tighter text-glow">
                    Elevate Your Trading with Precision Alerts
          </h1>
                  <h2 className="text-white text-sm font-normal leading-normal @[480px]:text-base @[480px]:font-normal @[480px]:leading-normal">
                    Unlock the power of informed trading with Autonama Research. Our cutting-edge platform delivers real-time alerts for crypto, forex, and stocks, empowering you to make strategic decisions and maximize your returns.
                  </h2>
                </div>
                <Link href="/dashboard">
                  <button className="btn-primary @[480px]:h-12 @[480px]:px-5 @[480px]:text-base @[480px]:font-bold @[480px]:leading-normal @[480px]:tracking-[0.015em] pulse-glow">
                    <span className="truncate">Get Started</span>
                  </button>
                </Link>
              </div>
            </div>
          </div>

          <h2 className="text-[22px] font-bold leading-tight tracking-tight px-4 pb-3 pt-5 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Alerts Overview</h2>
          <div className="flex flex-wrap gap-4 p-4">
            <div className="flex min-w-[158px] flex-1 flex-col gap-2 rounded-2xl p-8 transition-all duration-500 glass-hover" style={{ backgroundColor: 'var(--glass-bg)' }}>
              <p className="text-base font-medium leading-normal transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Crypto Alerts</p>
              <p className="tracking-light text-2xl font-bold leading-tight transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>120+</p>
            </div>
            <div className="flex min-w-[158px] flex-1 flex-col gap-2 rounded-2xl p-8 transition-all duration-500 glass-hover" style={{ backgroundColor: 'var(--glass-bg)' }}>
              <p className="text-base font-medium leading-normal transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Forex Alerts</p>
              <p className="tracking-light text-2xl font-bold leading-tight transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>150+</p>
            </div>
            <div className="flex min-w-[158px] flex-1 flex-col gap-2 rounded-2xl p-8 transition-all duration-500 glass-hover" style={{ backgroundColor: 'var(--glass-bg)' }}>
              <p className="text-base font-medium leading-normal transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Stock Alerts</p>
              <p className="tracking-light text-2xl font-bold leading-tight transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>100+</p>
          </div>
        </div>

          <h2 className="text-[22px] font-bold leading-tight tracking-tight px-4 pb-3 pt-5 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Key Features</h2>
          <div className="flex flex-col gap-10 px-4 py-10 @container">
            <div className="flex flex-col gap-4">
              <h1 className="tracking-light text-[32px] font-bold leading-tight @[480px]:text-4xl @[480px]:font-black @[480px]:leading-tight @[480px]:tracking-tighter max-w-[720px] transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
                Trade with Confidence
              </h1>
              <p className="text-base font-normal leading-normal max-w-[720px] transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                Autonama Research provides the tools and insights you need to succeed in the dynamic world of trading.
              </p>
          </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card float">
                <h3 className="text-lg font-bold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Real-time Alerts</h3>
                <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                  Get instant notifications for the best trading opportunities across multiple markets.
                </p>
        </div>

              <div className="card float" style={{ animationDelay: '0.2s' }}>
                <h3 className="text-lg font-bold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Advanced Analytics</h3>
                <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                  Deep market analysis with AI-powered insights and predictive modeling.
                </p>
              </div>

              <div className="card float" style={{ animationDelay: '0.4s' }}>
                <h3 className="text-lg font-bold mb-2 transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>Portfolio Optimization</h3>
                <p className="text-sm transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
                  Optimize your portfolio with our advanced algorithms and risk management tools.
                </p>
              </div>
            </div>
            </div>
        </div>
      </div>
    </div>
  );
}
