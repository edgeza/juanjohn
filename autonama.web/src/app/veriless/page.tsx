'use client';

import { useState, useEffect } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { ChevronRight, FileText, Shield, TrendingUp, Users, Zap, ArrowUp, ExternalLink, Download, BookOpen } from 'lucide-react';

// Table of Contents Component
const TableOfContents = ({ activeSection, onSectionClick }: { 
  activeSection: string; 
  onSectionClick: (section: string) => void; 
}) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const sections = [
    { id: 'overview', title: 'Overview', icon: BookOpen },
    { id: 'intro', title: 'Introduction & Market Thesis', icon: BookOpen },
    { id: 'product', title: 'Product Overview', icon: BookOpen },
    { id: 'treasury', title: 'Treasury Composition', icon: BookOpen },
    { id: 'strategy', title: 'Strategy Design', icon: TrendingUp },
    { id: 'nav', title: 'NAV & Oracle Design', icon: Shield },
    { id: 'mint', title: 'Mint/Redeem & Arbitrage', icon: Zap },
    { id: 'redemption-protections', title: 'Redemption Protections', icon: Shield },
    { id: 'fees-caps', title: 'Fee Policy & Caps', icon: TrendingUp },
    { id: 'nav-errors', title: 'NAV Error Policy', icon: Shield },
    { id: 'tokenomics', title: 'Tokenomics & Value Accrual', icon: TrendingUp },
    { id: 'liquidity', title: 'Liquidity & Market Making', icon: TrendingUp },
    { id: 'transparency', title: 'Transparency & Reporting', icon: Shield },
    { id: 'por', title: 'Proof-of-Reserves', icon: Shield },
    { id: 'governance', title: 'Governance & Community', icon: Users },
    { id: 'gov-process', title: 'Governance Process', icon: Users },
    { id: 'security', title: 'Security & Operations', icon: Shield },
    { id: 'risk', title: 'Risk Management', icon: Shield },
    { id: 'distribution', title: 'Distribution & Access', icon: Shield },
    { id: 'legal', title: 'Legal & Compliance', icon: FileText },
    { id: 'legal-outline', title: 'Legal Analysis Outline', icon: FileText },
    { id: 'legal-abstract', title: 'Legal Memo Abstract', icon: FileText },
    { id: 'architecture', title: 'Technical Architecture', icon: TrendingUp },
    { id: 'ops', title: 'Operational Resilience', icon: Shield },
    { id: 'sla', title: 'Service Levels', icon: Shield },
    { id: 'figures', title: 'Diagrams & Figures', icon: TrendingUp },
    { id: 'api', title: 'Data & API', icon: TrendingUp },
    { id: 'stress', title: 'Stress Scenarios', icon: TrendingUp },
    { id: 'bounty', title: 'Bug Bounty Program', icon: Shield },
    { id: 'interfaces', title: 'Smart Contract Interfaces', icon: TrendingUp },
    { id: 'appendix-a', title: 'Appendix A: Methodology', icon: BookOpen },
    { id: 'appendix-b', title: 'Appendix B: KPI Definitions', icon: BookOpen },
    { id: 'appendix-c', title: 'Appendix C: Glossary', icon: BookOpen },
    { id: 'risks', title: 'Risk Factors', icon: Shield },
    { id: 'notices', title: 'Legal Notices', icon: FileText },
    { id: 'team', title: 'Team & Credits', icon: Users },
    { id: 'accessibility', title: 'Accessibility', icon: Shield },
    { id: 'changelog', title: 'Changelog', icon: BookOpen },
  ];

  return (
    <nav className="sticky top-24 space-y-2">
      <h3 className="text-lg font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
        Contents
      </h3>
      {sections.map((section) => {
        const Icon = section.icon;
        return (
          <button
            key={section.id}
            onClick={() => onSectionClick(section.id)}
            className={`w-full text-left p-3 rounded-xl transition-all duration-300 flex items-center gap-3 group ${
              activeSection === section.id
                ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30'
                : 'hover:bg-gray-100/50 dark:hover:bg-white/5'
            }`}
            style={{
              color: activeSection === section.id 
                ? (isDark ? '#ffffff' : '#000000')
                : (isDark ? '#a0a0a0' : '#666666')
            }}
          >
            <Icon className="h-4 w-4" />
            <span className="font-medium">{section.title}</span>
            <ChevronRight className={`h-4 w-4 ml-auto transition-transform duration-300 ${
              activeSection === section.id ? 'rotate-90' : ''
            }`} />
          </button>
        );
      })}
    </nav>
  );
};

// Section Component
const Section = ({ id, title, children, className = '' }: {
  id: string;
  title: string;
  children: React.ReactNode;
  className?: string;
}) => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <section id={id} className={`py-12 ${className}`}>
      <div className="max-w-4xl mx-auto">
        <h2 
          className="text-3xl font-bold mb-8 text-center"
          style={{ color: isDark ? '#ffffff' : '#000000' }}
        >
          {title}
        </h2>
        <div 
          className="prose prose-lg max-w-none"
          style={{ color: isDark ? '#e0e0e0' : '#333333' }}
        >
          {children}
        </div>
      </div>
    </section>
  );
};

export default function VerilessPage() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [activeSection, setActiveSection] = useState('overview');

  // Intersection Observer for scroll spy
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: '-20% 0px -80% 0px' }
    );

    const sections = document.querySelectorAll('section[id]');
    sections.forEach((section) => observer.observe(section));

    return () => observer.disconnect();
  }, []);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="min-h-screen transition-all duration-500" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div 
          className="absolute inset-0"
          style={{
            background: isDark 
              ? 'radial-gradient(1200px 600px at 70% -10%, rgba(255,255,255,0.05), transparent 60%), radial-gradient(900px 500px at -10% 0%, rgba(255,255,255,0.04), transparent 50%)'
              : 'radial-gradient(1200px 600px at 70% -10%, rgba(0,0,0,0.02), transparent 60%), radial-gradient(900px 500px at -10% 0%, rgba(0,0,0,0.02), transparent 50%)'
          }}
        />
        
        <div className="relative z-10 pt-20 pb-16 px-6">
          <div className="max-w-6xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border mb-6" style={{
              borderColor: isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)',
              backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
            }}>
              <span className="text-sm font-medium" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                Draft v0.9 • Living document
              </span>
            </div>
            
                         <h1 
               className="text-5xl md:text-7xl font-bold mb-6 leading-tight"
               style={{ color: isDark ? '#ffffff' : '#000000' }}
             >
               Project Veriless
             </h1>
            <p 
              className="text-xl md:text-2xl mb-8 max-w-4xl mx-auto leading-relaxed"
              style={{ color: isDark ? '#e0e0e0' : '#666666' }}
            >
              An On‑Chain, Actively Managed L1 Accumulation Token
            </p>
            <p 
              className="text-lg mb-12 max-w-3xl mx-auto"
              style={{ color: isDark ? '#a0a0a0' : '#888888' }}
            >
              A rules‑based, transparency‑first digital asset product designed to harvest cycle volatility across leading L1s.
            </p>

            {/* Meta Information */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 max-w-4xl mx-auto">
              <div className="text-center p-4 rounded-2xl glass" style={{
                backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
              }}>
                <div className="text-sm mb-2" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Date</div>
                <div className="font-semibold" style={{ color: isDark ? '#ffffff' : '#000000' }}>2025‑08‑12</div>
              </div>
              <div className="text-center p-4 rounded-2xl glass" style={{
                backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
              }}>
                <div className="text-sm mb-2" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Contacts</div>
                <div className="font-semibold text-sm" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                  founders@veriless.org
                </div>
              </div>
              <div className="text-center p-4 rounded-2xl glass" style={{
                backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
              }}>
                <div className="text-sm mb-2" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Status</div>
                <div className="font-semibold" style={{ color: isDark ? '#ffffff' : '#000000' }}>Active Development</div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="btn-primary text-lg px-8 py-4 flex items-center gap-3">
                <Download className="h-5 w-5" />
                <span>Download PDF</span>
              </button>
              <button className="btn-secondary text-lg px-8 py-4 flex items-center gap-3">
                <ExternalLink className="h-5 w-5" />
                <span>View on GitHub</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="px-6 py-8">
        <div className="max-w-4xl mx-auto">
          <div 
            className="p-6 rounded-2xl border-l-4 border-red-500/50"
            style={{
              backgroundColor: isDark ? 'rgba(255,0,0,0.1)' : 'rgba(255,0,0,0.05)',
              borderColor: isDark ? 'rgba(255,0,0,0.3)' : 'rgba(255,0,0,0.2)'
            }}
          >
            <div className="flex items-start gap-3">
              <Shield className="h-6 w-6 mt-1" style={{ color: '#ef4444' }} />
              <div>
                <h3 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                  Important Disclaimer
                </h3>
                <p className="text-sm" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                  Veriless is not an ETF or a registered security, and nothing in this document constitutes investment advice, 
                  an offer, or a solicitation. Digital assets are highly volatile and may result in total loss. 
                  Access may be restricted by jurisdiction.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
            {/* Table of Contents */}
            <div className="lg:col-span-1">
              <TableOfContents 
                activeSection={activeSection} 
                onSectionClick={scrollToSection} 
              />
            </div>

            {/* Content */}
            <div className="lg:col-span-3">
              <Section id="overview" title="Why Trust Veriless?">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  <div className="p-6 rounded-2xl glass" style={{
                    backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                    border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                  }}>
                    <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                      Security & Audits
                    </h3>
                    <ul className="space-y-2 text-sm">
                      <li>• Two independent security audits</li>
                      <li>• One mechanism review</li>
                      <li>• Full reports published pre‑mainnet</li>
                    </ul>
                  </div>
                  <div className="p-6 rounded-2xl glass" style={{
                    backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                    border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                  }}>
                    <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                      Transparency
                    </h3>
                    <ul className="space-y-2 text-sm">
                      <li>• Live proof‑of‑reserves</li>
                      <li>• Real‑time NAV reconciliation</li>
                      <li>• Public dashboards</li>
                    </ul>
                  </div>
                </div>

                <div className="space-y-6">
                  <h3 className="text-2xl font-semibold" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                    Executive Summary
                  </h3>
                  <div className="space-y-4">
                    <div className="p-4 rounded-xl" style={{
                      backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'
                    }}>
                      <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>Problem</h4>
                      <p style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                        Most meme tokens lack intrinsic value; many retail investors buy tops and sell bottoms. 
                        Access to disciplined, rules‑based cycle strategies is limited and typically off‑chain and gated.
                        <strong>Key Issues:</strong>
                      </p>
                      <ul className="mt-2 space-y-1 text-sm" style={{ color: isDark ? '#c0c0c0' : '#555555' }}>
                        <li>• 95% of retail investors lose money due to emotional trading</li>
                        <li>• Traditional wealth management requires $100K+ minimums</li>
                        <li>• Geographic restrictions limit access to sophisticated strategies</li>
                        <li>• Lack of transparency in off‑chain managed products</li>
                        <li>• No systematic approach to cycle volatility harvesting</li>
                      </ul>
                    </div>
                    <div className="p-4 rounded-xl" style={{
                      backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'
                    }}>
                      <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>Solution</h4>
                      <p style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                        <strong>Veriless</strong> is an on‑chain token whose treasury accumulates a diversified basket of L1 cryptoassets 
                        and systematically harvests cycle volatility using a transparent, rules‑based framework.
                      </p>
                      <ul className="mt-2 space-y-1 text-sm" style={{ color: isDark ? '#c0c0c0' : '#555555' }}>
                        <li>• <strong>On‑chain transparency:</strong> Real‑time proof‑of‑reserves and NAV</li>
                        <li>• <strong>Rules‑based strategy:</strong> Mathematical framework removes emotion</li>
                        <li>• <strong>Cycle harvesting:</strong> Buy statistically cheap, sell statistically rich</li>
                        <li>• <strong>Access democratization:</strong> No minimums, global availability</li>
                        <li>• <strong>Risk management:</strong> Systematic position sizing and limits</li>
                      </ul>
                    </div>
                    <div className="p-4 rounded-xl" style={{
                      backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'
                    }}>
                      <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>Expected Outcomes</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
                        <div className="text-center p-3 rounded-lg" style={{
                          backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'
                        }}>
                          <div className="text-2xl font-bold mb-1" style={{ color: isDark ? '#ffffff' : '#000000' }}>15-25%</div>
                          <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Annual Alpha vs Passive</div>
                        </div>
                        <div className="text-center p-3 rounded-lg" style={{
                          backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'
                        }}>
                          <div className="text-2xl font-bold mb-1" style={{ color: isDark ? '#ffffff' : '#000000' }}>30-40%</div>
                          <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Drawdown Reduction</div>
                        </div>
                        <div className="text-center p-3 rounded-lg" style={{
                          backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'
                        }}>
                          <div className="text-2xl font-bold mb-1" style={{ color: isDark ? '#ffffff' : '#000000' }}>2.5-3.5</div>
                          <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Sharpe Ratio Target</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                             </Section>

               <Section id="intro" title="Introduction and Market Thesis">
                 <div className="space-y-6">
                   <p className="text-lg" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                     Retail‑led "meme" cycles demonstrate strong attention‑driven booms and busts. While long‑term adoption trends for leading L1s (Bitcoin, Ethereum, Solana) remain intact, path dependency often leads to poor realized returns for undisciplined holders. Traditional ETFs and managed products exist off‑chain, with high minimums, geography constraints, and reduced transparency.
                   </p>
                   <p className="text-lg" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                     Veriless brings a disciplined, rules‑based approach on‑chain: a token that represents a claim on a treasury of L1 assets, with an active policy aiming to harvest cycle volatility by buying when prices are statistically "cheap" relative to long‑horizon trends and trimming when statistically "rich." The objective is to improve risk‑adjusted returns versus passive holding across full cycles while maintaining on‑chain transparency and access.
                   </p>
                 </div>
               </Section>

               <Section id="product" title="Product Overview">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Product Structure
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• ERC‑20‑compatible vault share token</li>
                         <li>• Pro‑rata claim on underlying treasury NAV</li>
                         <li>• Rules‑based, regression‑band framework</li>
                         <li>• Optional passive core and active sleeve</li>
                       </ul>
                     </div>
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Key Features
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• Real‑time proof‑of‑reserves</li>
                         <li>• Oracle‑sourced prices with TWAP</li>
                         <li>• Permissionless mint/redeem at NAV</li>
                         <li>• Governance‑controlled parameters</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="treasury" title="Treasury Composition and Target Exposures">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Initial Asset Set
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• BTC, ETH, SOL</li>
                         <li>• Governance‑expandable</li>
                         <li>• Liquidity and custody screening</li>
                         <li>• Regulatory compliance checks</li>
                       </ul>
                     </div>
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Target Weights
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• BTC: 50–70%</li>
                         <li>• ETH: 20–40%</li>
                         <li>• SOL: 5–20%</li>
                         <li>• Stables/cash: 0–15%</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

                               <Section id="strategy" title="Strategy Design">
                 <div className="space-y-6">
                   <p className="text-lg" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                     Veriless uses a long‑horizon trend model to create regression bands around log‑price. 
                     While exact parameters remain proprietary, the framework and controls are transparent.
                   </p>

                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Signal Framework
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• Fit smooth trend to log price using regression</li>
                         <li>• Define residuals and estimate dispersion</li>
                         <li>• Compute z‑scores for buy/sell signals</li>
                         <li>• Accumulate below bands, distribute above</li>
                       </ul>
                     </div>
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Risk Limits
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• Active sleeve: up to 50% of treasury</li>
                         <li>• Daily turnover caps: 5–10% of NAV</li>
                         <li>• Per‑asset concentration limits</li>
                         <li>• Circuit breakers for extreme events</li>
                       </ul>
                     </div>
                   </div>

                   {/* Mathematical Framework Details */}
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       Mathematical Framework
                     </h3>
                     <div className="space-y-4">
                       <div>
                         <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>1. Trend Fitting</h4>
                         <p className="text-sm mb-2" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                           Fit a smooth trend function T(t) to log price data using robust regression:
                         </p>
                         <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                           log(P(t)) = T(t) + ε(t)
                         </div>
                         <p className="text-sm mt-2" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
                           Where ε(t) represents the residual component around the trend.
                         </p>
                       </div>
                       
                       <div>
                         <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>2. Regression Bands</h4>
                         <p className="text-sm mb-2" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                           Define buy/sell bands using statistical dispersion:
                         </p>
                         <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                           Upper Band: T(t) + k × σ(t)<br/>
                           Lower Band: T(t) - k × σ(t)
                         </div>
                         <p className="text-sm mt-2" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
                           Where k is the z‑score threshold (typically 1.5-2.0) and σ(t) is the rolling volatility estimate.
                         </p>
                       </div>

                       <div>
                         <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>3. Signal Generation</h4>
                         <p className="text-sm mb-2" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                           Generate trading signals based on price position relative to bands:
                         </p>
                         <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                           Buy Signal: log(P(t)) < T(t) - k × σ(t)<br/>
                           Sell Signal: log(P(t)) > T(t) + k × σ(t)<br/>
                           Hold: T(t) - k × σ(t) ≤ log(P(t)) ≤ T(t) + k × σ(t)
                         </div>
                       </div>

                       <div>
                         <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>4. Position Sizing</h4>
                         <p className="text-sm mb-2" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                           Dynamic position sizing based on signal strength:
                         </p>
                         <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                           Position Size = Base Allocation × Signal Strength × Risk Budget
                         </div>
                         <p className="text-sm mt-2" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
                           Signal strength is normalized from 0 to 1 based on distance from bands.
                         </p>
                       </div>
                     </div>
                   </div>

                   {/* Risk Management Details */}
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       Risk Management Framework
                     </h3>
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                       <div>
                         <h4 className="font-semibold mb-3" style={{ color: isDark ? '#ffffff' : '#000000' }}>Position Limits</h4>
                         <ul className="space-y-2 text-sm">
                           <li>• <strong>Active Sleeve:</strong> Maximum 50% of treasury NAV</li>
                           <li>• <strong>Per‑Asset Cap:</strong> Maximum 25% in single asset</li>
                           <li>• <strong>Leverage:</strong> Maximum 1.2x effective exposure</li>
                           <li>• <strong>Cash Buffer:</strong> Minimum 5% liquid reserves</li>
                         </ul>
                       </div>
                       <div>
                         <h4 className="font-semibold mb-3" style={{ color: isDark ? '#ffffff' : '#000000' }}>Turnover Controls</h4>
                         <ul className="space-y-2 text-sm">
                           <li>• <strong>Daily Limit:</strong> Maximum 10% of NAV</li>
                           <li>• <strong>Weekly Limit:</strong> Maximum 25% of NAV</li>
                           <li>• <strong>Monthly Limit:</strong> Maximum 50% of NAV</li>
                           <li>• <strong>Cooldown:</strong> 24h after hitting limits</li>
                         </ul>
                       </div>
                     </div>
                     
                     <div className="mt-6">
                       <h4 className="font-semibold mb-3" style={{ color: isDark ? '#ffffff' : '#000000' }}>Circuit Breakers</h4>
                       <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                         <div className="text-center p-3 rounded-lg" style={{
                           backgroundColor: isDark ? 'rgba(255,0,0,0.1)' : 'rgba(255,0,0,0.05)'
                         }}>
                           <div className="text-lg font-bold mb-1" style={{ color: '#ef4444' }}>Level 1</div>
                           <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
                             <div>15% daily drawdown</div>
                             <div>Action: Reduce active sleeve</div>
                           </div>
                         </div>
                         <div className="text-center p-3 rounded-lg" style={{
                           backgroundColor: isDark ? 'rgba(255,165,0,0.1)' : 'rgba(255,165,0,0.05)'
                         }}>
                           <div className="text-lg font-bold mb-1" style={{ color: '#f97316' }}>Level 2</div>
                           <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
                             <div>25% daily drawdown</div>
                             <div>Action: Pause new positions</div>
                           </div>
                         </div>
                         <div className="text-center p-3 rounded-lg" style={{
                           backgroundColor: isDark ? 'rgba(255,0,0,0.2)' : 'rgba(255,0,0,0.1)'
                         }}>
                           <div className="text-lg font-bold mb-1" style={{ color: '#dc2626' }}>Level 3</div>
                           <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
                             <div>35% daily drawdown</div>
                             <div>Action: Emergency stop</div>
                           </div>
                         </div>
                       </div>
                     </div>
                   </div>
                 </div>
               </Section>

              <Section id="nav" title="NAV and Oracle Design">
                <div className="space-y-6">
                  <div className="p-6 rounded-2xl glass" style={{
                    backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                    border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                  }}>
                    <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                      NAV Definition
                    </h3>
                    <p className="mb-4" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                      Let treasury holdings value be <code className="bg-gray-200 dark:bg-gray-800 px-2 py-1 rounded">V<sub>t</sub></code> in USD. 
                      With <code className="bg-gray-200 dark:bg-gray-800 px-2 py-1 rounded">S<sub>t</sub></code> shares outstanding, NAV per share is:
                    </p>
                    <div className="bg-gray-100 dark:bg-gray-900 p-4 rounded-xl text-center">
                      <code className="text-lg font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                        NAV<sub>t</sub> = (V<sub>t</sub> − L<sub>t</sub>) / S<sub>t</sub>
                      </code>
                    </div>
                    <p className="mt-3 text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
                      Where L<sub>t</sub> represents liabilities (fees, expenses, and any outstanding obligations).
                    </p>
                  </div>

                  {/* Oracle Architecture */}
                  <div className="p-6 rounded-2xl glass" style={{
                    backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                    border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                  }}>
                    <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                      Oracle Architecture
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold mb-3" style={{ color: isDark ? '#ffffff' : '#000000' }}>Primary Sources</h4>
                        <ul className="space-y-2 text-sm">
                          <li>• <strong>Chainlink:</strong> BTC/USD, ETH/USD, SOL/USD</li>
                          <li>• <strong>Pyth Network:</strong> High-frequency price feeds</li>
                          <li>• <strong>Update Frequency:</strong> Every 15 seconds</li>
                          <li>• <strong>Heartbeat:</strong> Maximum 60s staleness</li>
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-semibold mb-3" style={{ color: isDark ? '#ffffff' : '#000000' }}>Secondary Sources</h4>
                        <ul className="space-y-2 text-sm">
                          <li>• <strong>DEX TWAPs:</strong> Uniswap V3, SushiSwap</li>
                          <li>• <strong>CEX Indices:</strong> Binance, Coinbase, Kraken</li>
                          <li>• <strong>Aggregation:</strong> Volume-weighted median</li>
                          <li>• <strong>Fallback:</strong> Last known good price</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Price Aggregation Algorithm */}
                  <div className="p-6 rounded-2xl glass" style={{
                    backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                    border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                  }}>
                    <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                      Price Aggregation Algorithm
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>1. Data Validation</h4>
                        <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                          <div>// Check staleness and deviation</div>
                          <div>if (timestamp - lastUpdate) > MAX_STALENESS:</div>
                          <div>  markSourceAsStale(source)</div>
                          <div>if abs(price - medianPrice) > MAX_DEVIATION:</div>
                          <div>  markSourceAsOutlier(source)</div>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>2. Weighted Aggregation</h4>
                        <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                          <div>// Volume-weighted median with outlier rejection</div>
                          <div>validPrices = filterOutliers(prices)</div>
                          <div>finalPrice = weightedMedian(validPrices, volumes)</div>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>3. NAV Calculation</h4>
                        <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                          <div>// Real-time NAV computation</div>
                          <div>for each asset in treasury:</div>
                          <div>  assetValue = quantity × finalPrice</div>
                          <div>totalValue = sum(assetValues)</div>
                          <div>navPerShare = (totalValue - liabilities) / sharesOutstanding</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Error Handling and Monitoring */}
                  <div className="p-6 rounded-2xl glass" style={{
                    backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                    border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                  }}>
                    <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                      Error Handling and Monitoring
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h4 className="font-semibold mb-3" style={{ color: isDark ? '#ffffff' : '#000000' }}>Error Tolerances</h4>
                        <ul className="space-y-2 text-sm">
                          <li>• <strong>NAV Error:</strong> Maximum 10 basis points</li>
                          <li>• <strong>Price Deviation:</strong> Maximum 5% from median</li>
                          <li>• <strong>Oracle Staleness:</strong> Maximum 60 seconds</li>
                          <li>• <strong>Restatement Window:</strong> Within 24 hours</li>
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-semibold mb-3" style={{ color: isDark ? '#ffffff' : '#000000' }}>Monitoring Systems</h4>
                        <ul className="space-y-2 text-sm">
                          <li>• <strong>Real-time Alerts:</strong> Price deviation > 3%</li>
                          <li>• <strong>Oracle Health:</strong> Continuous monitoring</li>
                          <li>• <strong>NAV Reconciliation:</strong> Hourly checks</li>
                          <li>• <strong>Discrepancy Logging:</strong> Full audit trail</li>
                        </ul>
                      </div>
                    </div>
                    
                    <div className="mt-6">
                      <h4 className="font-semibold mb-3" style={{ color: isDark ? '#ffffff' : '#000000' }}>Emergency Procedures</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center p-3 rounded-lg" style={{
                          backgroundColor: isDark ? 'rgba(255,165,0,0.1)' : 'rgba(255,165,0,0.05)'
                        }}>
                          <div className="text-lg font-bold mb-1" style={{ color: '#f97316' }}>Warning</div>
                          <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
                            <div>5% price deviation</div>
                            <div>Action: Alert team</div>
                          </div>
                        </div>
                        <div className="text-center p-3 rounded-lg" style={{
                          backgroundColor: isDark ? 'rgba(255,0,0,0.1)' : 'rgba(255,0,0,0.05)'
                        }}>
                          <div className="text-lg font-bold mb-1" style={{ color: '#ef4444' }}>Critical</div>
                          <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
                            <div>10% price deviation</div>
                            <div>Action: Pause mint/redeem</div>
                          </div>
                        </div>
                        <div className="text-center p-3 rounded-lg" style={{
                          backgroundColor: isDark ? 'rgba(255,0,0,0.2)' : 'rgba(255,0,0,0.1)'
                        }}>
                          <div className="text-lg font-bold mb-1" style={{ color: '#dc2626' }}>Emergency</div>
                          <div className="text-sm" style={{ color: isDark ? '#a0e0e0' : '#666666' }}>
                            <div>Oracle failure</div>
                            <div>Action: Emergency stop</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </Section>

                             <Section id="mint" title="Mint, Redeem, and Arbitrage">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Mint Process
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• Deposit whitelisted assets or stables</li>
                         <li>• Receive Veriless at NAV + mint fee</li>
                         <li>• Settlement: T+0 to T+1</li>
                         <li>• Pro‑rata fills during stress</li>
                       </ul>
                     </div>
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Redemption
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• Burn Veriless tokens</li>
                         <li>• Receive basket assets or stables</li>
                         <li>• NAV minus redeem fee</li>
                         <li>• In‑kind option during stress</li>
                       </ul>
                     </div>
                   </div>

                   {/* Detailed Fee Structure */}
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       Fee Structure (Governance‑Capped)
                     </h3>
                     <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                       <div className="text-center">
                         <div className="text-2xl font-bold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>0.75%</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Management Fee (p.a.)</div>
                       </div>
                       <div className="text-center">
                         <div className="text-2xl font-bold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>10%</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Performance Fee</div>
                       </div>
                       <div className="text-center">
                         <div className="text-2xl font-bold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>10 bps</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Mint/Redeem</div>
                       </div>
                     </div>
                     
                     <div className="space-y-4">
                       <div>
                         <h4 className="font-semibold mb-3" style={{ color: isDark ? '#ffffff' : '#000000' }}>Management Fee Calculation</h4>
                         <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                           <div>Daily Fee = NAV × 0.75% ÷ 365</div>
                           <div>Example: $1M NAV = $20.55 daily fee</div>
                         </div>
                       </div>
                       
                       <div>
                         <h4 className="font-semibold mb-3" style={{ color: isDark ? '#ffffff' : '#000000' }}>Performance Fee Calculation</h4>
                         <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                           <div>Performance Fee = (Current NAV - High Water Mark) × 10%</div>
                           <div>High Water Mark: Highest NAV since last fee collection</div>
                         </div>
                       </div>

                       <div>
                         <h4 className="font-semibold mb-3" style={{ color: isDark ? '#ffffff' : '#000000' }}>Mint/Redeem Fee Examples</h4>
                         <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                           <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg">
                             <div className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>Mint Example:</div>
                             <div className="text-sm" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                               <div>Deposit: $10,000</div>
                               <div>Mint Fee: $10 (10 bps)</div>
                               <div>Net Investment: $9,990</div>
                               <div>Shares Received: $9,990 ÷ NAV</div>
                             </div>
                           </div>
                           <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg">
                             <div className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>Redeem Example:</div>
                             <div className="text-sm" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                               <div>Redeem: $10,000 worth</div>
                               <div>Redeem Fee: $10 (10 bps)</div>
                               <div>Net Proceeds: $9,990</div>
                               <div>Assets Received: $9,990 worth</div>
                             </div>
                           </div>
                         </div>
                       </div>
                     </div>
                   </div>

                   {/* Arbitrage Mechanics */}
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       Arbitrage Mechanics
                     </h3>
                     <div className="space-y-4">
                       <div>
                         <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>Premium/Discount Arbitrage</h4>
                         <p className="text-sm mb-3" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                           When Veriless trades above NAV (premium), arbitrageurs can:
                         </p>
                         <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                           <div>1. Mint Veriless at NAV + 10 bps</div>
                           <div>2. Sell on secondary market at premium</div>
                           <div>3. Profit = Premium - 10 bps - gas costs</div>
                         </div>
                       </div>
                       
                       <div>
                         <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>Discount Arbitrage</h4>
                         <p className="text-sm mb-3" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                           When Veriless trades below NAV (discount), arbitrageurs can:
                         </p>
                         <div className="bg-gray-100 dark:bg-gray-900 p-3 rounded-lg text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                           <div>1. Buy Veriless at discount</div>
                           <div>2. Redeem at NAV - 10 bps</div>
                           <div>3. Profit = Discount - 10 bps - gas costs</div>
                         </div>
                       </div>

                       <div>
                         <h4 className="font-semibold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>Arbitrage Thresholds</h4>
                         <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                           <div className="text-center p-3 rounded-lg" style={{
                             backgroundColor: isDark ? 'rgba(0,255,0,0.1)' : 'rgba(0,255,0,0.05)'
                           }}>
                             <div className="text-lg font-bold mb-1" style={{ color: '#22c55e' }}>Premium > 15 bps</div>
                             <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
                               <div>Profitable to mint</div>
                               <div>Arbitrageurs active</div>
                             </div>
                           </div>
                           <div className="text-center p-3 rounded-lg" style={{
                             backgroundColor: isDark ? 'rgba(255,0,0,0.1)' : 'rgba(255,0,0,0.05)'
                           }}>
                             <div className="text-lg font-bold mb-1" style={{ color: '#ef4444' }}>Discount > 15 bps</div>
                             <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
                               <div>Profitable to redeem</div>
                               <div>Arbitrageurs active</div>
                             </div>
                           </div>
                         </div>
                       </div>
                     </div>
                   </div>
                 </div>
                              </Section>

               <Section id="redemption-protections" title="Redemption Protections">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Queues & Gates
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• Daily redemption cap of Q% NAV</li>
                         <li>• Excess queued FCFS</li>
                         <li>• Pro‑rata within window</li>
                         <li>• Anti‑dilution protection</li>
                       </ul>
                     </div>
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Swing Pricing
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• Anti‑dilution adjustment</li>
                         <li>• When net flows exceed T%</li>
                         <li>• Formula disclosed pre‑trade</li>
                         <li>• In‑kind option during stress</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="fees-caps" title="Fee Policy & Caps">
                 <div className="space-y-6">
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       Fee Structure (Governance‑Capped)
                     </h3>
                     <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                       <div className="text-center">
                         <div className="text-2xl font-bold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>0.75%</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Management Fee (p.a.)</div>
                       </div>
                       <div className="text-center">
                         <div className="text-2xl font-bold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>10%</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Performance Fee</div>
                       </div>
                       <div className="text-center">
                         <div className="text-2xl font-bold mb-2" style={{ color: isDark ? '#ffffff' : '#000000' }}>10 bps</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Mint/Redeem</div>
                       </div>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="nav-errors" title="NAV Error Policy">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Error Tolerances
                       </h3>
                       <ul className="space-y-2">
                         <li>• NAV error tolerance: 10 bps</li>
                         <li>• Restatement within 24h if exceeded</li>
                         <li>• Daily NAV cut‑off time HH:MM UTC</li>
                         <li>• Holidays listed on status page</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Stale Price Handling
                       </h3>
                       <ul className="space-y-2">
                         <li>• Primary and fallback oracle checks</li>
                         <li>• Suspend mint/redeem if both stale</li>
                         <li>• Display banner for users</li>
                         <li>• FX handling for non‑USD pairs</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="tokenomics" title="Tokenomics and Value Accrual">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Token Structure
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• ERC‑20‑compatible vault share</li>
                         <li>• Elastic supply policy</li>
                         <li>• Minted/burned on primary activity</li>
                         <li>• Tracks NAV changes</li>
                       </ul>
                     </div>
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Allocations
                       </h3>
                       <ul className="space-y-2 text-sm">
                         <li>• Community & Liquidity: 40%</li>
                         <li>• Treasury/Reserves: 25%</li>
                         <li>• Team & Contributors: 20%</li>
                         <li>• Ecosystem/Advisors: 10%</li>
                         <li>• Bug Bounty/Grants: 5%</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="liquidity" title="Liquidity and Market Making">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Initial Pools
                       </h3>
                       <ul className="space-y-2">
                         <li>• Pair with leading stables</li>
                         <li>• Major L1 asset pairs</li>
                         <li>• Top DEXs for distribution</li>
                         <li>• Target depth: $2–5M per pool</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Market Making
                       </h3>
                       <ul className="space-y-2">
                         <li>• Non‑custodial arrangements</li>
                         <li>• Clear disclosure of inventory</li>
                         <li>• Time‑bounded LM programs</li>
                         <li>• Decaying emissions</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="transparency" title="Transparency and Reporting">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Proof‑of‑Reserves
                       </h3>
                       <ul className="space-y-2">
                         <li>• On‑chain real‑time ledger</li>
                         <li>• Merkle proofs for verification</li>
                         <li>• Public dashboard access</li>
                         <li>• Third‑party attestations</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Reporting Cadence
                       </h3>
                       <ul className="space-y-2">
                         <li>• NAV: Realtime (99.9% within 60s)</li>
                         <li>• Holdings: Realtime</li>
                         <li>• Trades: T+24–72h</li>
                         <li>• Monthly fact sheets</li>
                         <li>• Quarterly letters</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="por" title="Proof‑of‑Reserves">
                 <div className="space-y-6">
                   <p className="text-lg" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                     Veriless publishes real‑time holdings on‑chain with Merkle proofs that can be independently verified. The proof‑of‑reserves contract exposes the current Merkle root and historical roots.
                   </p>
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       Data Schema
                     </h3>
                     <div className="bg-gray-100 dark:bg-gray-900 p-4 rounded-xl text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       <div>Chain ID, timestamp, assets array</div>
                       <div>Merkle root, inventory hash</div>
                       <div>NAV USD, shares outstanding</div>
                       <div>Independent verification possible</div>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="governance" title="Governance and Community">
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                        Governance Model
                      </h3>
                      <ul className="space-y-2">
                        <li>• Phase 1: Council + multisig guardian</li>
                        <li>• Phase 2: On‑chain token voting</li>
                        <li>• Bounded parameters and timelocks</li>
                        <li>• Emergency pause for security incidents</li>
                      </ul>
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                        Governable Parameters
                      </h3>
                      <ul className="space-y-2">
                        <li>• Asset list and weight bands</li>
                        <li>• Fee caps and active sleeve bounds</li>
                        <li>• Turnover caps and disclosure lags</li>
                        <li>• Oracle sources and emergency procedures</li>
                      </ul>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl glass" style={{
                    backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                    border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                  }}>
                    <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                      Proposal Lifecycle
                    </h3>
                    <div className="flex items-center justify-center gap-4 text-sm">
                      <div className="text-center">
                        <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center mx-auto mb-2">1</div>
                        <div>Forum Discussion</div>
                      </div>
                      <ArrowUp className="h-4 w-4 transform rotate-90" />
                      <div className="text-center">
                        <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center mx-auto mb-2">2</div>
                        <div>Snapshot Signaling</div>
                      </div>
                      <ArrowUp className="h-4 w-4 transform rotate-90" />
                      <div className="text-center">
                        <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center mx-auto mb-2">3</div>
                        <div>On‑chain Vote</div>
                      </div>
                      <ArrowUp className="h-4 w-4 transform rotate-90" />
                      <div className="text-center">
                        <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center mx-auto mb-2">4</div>
                        <div>Timelock Execution</div>
                      </div>
                    </div>
                  </div>
                </div>
                             </Section>

               <Section id="gov-process" title="Governance Process and Parameter Bounds">
                 <div className="space-y-6">
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       Proposal Lifecycle
                     </h3>
                     <div className="flex items-center justify-center gap-4 text-sm">
                       <div className="text-center">
                         <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center mx-auto mb-2">1</div>
                         <div>Forum Discussion</div>
                       </div>
                       <ArrowUp className="h-4 w-4 transform rotate-90" />
                       <div className="text-center">
                         <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center mx-auto mb-2">2</div>
                         <div>Snapshot Signaling</div>
                       </div>
                       <ArrowUp className="h-4 w-4 transform rotate-90" />
                       <div className="text-center">
                         <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center mx-auto mb-2">3</div>
                         <div>On‑chain Vote</div>
                       </div>
                       <ArrowUp className="h-4 w-4 transform rotate-90" />
                       <div className="text-center">
                         <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center mx-auto mb-2">4</div>
                         <div>Timelock Execution</div>
                       </div>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="risk" title="Risk Management">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Risk Taxonomy
                       </h3>
                       <ul className="space-y-2">
                         <li>• Market, liquidity, execution</li>
                         <li>• Oracle, custody, smart contract</li>
                         <li>• Regulatory, operational</li>
                         <li>• Quantitative limits and alerts</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Stress Testing
                       </h3>
                       <ul className="space-y-2">
                         <li>• Historical crises scenarios</li>
                         <li>• Liquidity modeling</li>
                         <li>• Oracle failure drills</li>
                         <li>• Custody incident exercises</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="distribution" title="Distribution & Access Controls">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Primary Market
                       </h3>
                       <ul className="space-y-2">
                         <li>• May require KYC/AML</li>
                         <li>• Restricted regions blocked</li>
                         <li>• Compliance pathway options</li>
                         <li>• User attestations required</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Secondary Market
                       </h3>
                       <ul className="space-y-2">
                         <li>• User responsibility</li>
                         <li>• Front‑end geofencing</li>
                         <li>• Terms acknowledgment</li>
                         <li>• Risk factor disclosure</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="security" title="Security, Custody, and Operations">
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="p-6 rounded-2xl glass" style={{
                      backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                      border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                    }}>
                      <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                        Custody & Signers
                      </h3>
                      <ul className="space-y-2 text-sm">
                        <li>• MPC/multisig with 4‑eyes approval</li>
                        <li>• Geographic dispersion across ≥3 regions</li>
                        <li>• Hardware security keys and FIDO2</li>
                        <li>• Rotation every 6–12 months</li>
                      </ul>
                    </div>
                    <div className="p-6 rounded-2xl glass" style={{
                      backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                      border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                    }}>
                      <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                        Smart Contracts
                      </h3>
                      <ul className="space-y-2 text-sm">
                        <li>• Minimal upgradability</li>
                        <li>• Proxy with timelock</li>
                        <li>• Narrowly scoped admin powers</li>
                        <li>• Emergency pause only</li>
                      </ul>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl glass" style={{
                    backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                    border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                  }}>
                    <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                      Bug Bounty Program
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                      <div>
                        <div className="text-lg font-bold mb-1" style={{ color: '#ef4444' }}>Critical</div>
                        <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>$50K–$250K</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold mb-1" style={{ color: '#f97316' }}>High</div>
                        <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>$10K–$50K</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold mb-1" style={{ color: '#eab308' }}>Medium</div>
                        <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>$2K–$10K</div>
                      </div>
                      <div>
                        <div className="text-lg font-bold mb-1" style={{ color: '#22c55e' }}>Low</div>
                        <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>$200–$2K</div>
                      </div>
                    </div>
                  </div>
                </div>
                             </Section>

               <Section id="legal-outline" title="Legal Analysis Outline">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Howey Factors
                       </h3>
                       <ul className="space-y-2">
                         <li>• Investment of money analysis</li>
                         <li>• Common enterprise assessment</li>
                         <li>• Expectation of profits</li>
                         <li>• Efforts of others evaluation</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Regulatory Considerations
                       </h3>
                       <ul className="space-y-2">
                         <li>• 40‑Act/UCITS/CTA assessment</li>
                         <li>• Registration requirements</li>
                         <li>• Mitigation strategies</li>
                         <li>• Future registration roadmap</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="legal-abstract" title="Legal Memo Abstract">
                 <div className="space-y-6">
                   <p className="text-lg" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                     Summary of counsel's analysis (non‑binding, subject to change):
                   </p>
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <ul className="space-y-2">
                       <li>• Positioning as vault share reduces securities law risks</li>
                       <li>• Primary market access requires KYC/AML in multiple regions</li>
                       <li>• No derivatives/leverage at launch</li>
                       <li>• Full legal memos to be linked upon publication</li>
                     </ul>
                   </div>
                 </div>
               </Section>

               <Section id="architecture" title="Technical Architecture">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Core Contracts
                       </h3>
                       <ul className="space-y-2">
                         <li>• Vault share token</li>
                         <li>• Treasury manager</li>
                         <li>• Config registry</li>
                         <li>• Mint/redeem gateway</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Infrastructure
                       </h3>
                       <ul className="space-y-2">
                         <li>• Decentralized oracles</li>
                         <li>• Off‑chain keepers</li>
                         <li>• Subgraph/indexer</li>
                         <li>• Security modules</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="ops" title="Operational Resilience">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Business Continuity
                       </h3>
                       <ul className="space-y-2">
                         <li>• Redundant keepers with failover</li>
                         <li>• Cold backup of keys</li>
                         <li>• Shamir Secret Sharing</li>
                         <li>• Regular recovery drills</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Change Management
                       </h3>
                       <ul className="space-y-2">
                         <li>• Formal release process</li>
                         <li>• Canary deploys on testnet</li>
                         <li>• Rollback procedures</li>
                         <li>• Vendor risk assessments</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="sla" title="Service Levels">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Performance Targets
                       </h3>
                       <ul className="space-y-2">
                         <li>• NAV update: 99.9% within 60s</li>
                         <li>• Proof‑of‑reserves: 5min batches</li>
                         <li>• Incident response: P1 within 15min</li>
                         <li>• Governance timelock: 48h minimum</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Error Budgets
                       </h3>
                       <ul className="space-y-2">
                         <li>• Monthly tracking</li>
                         <li>• Public post‑mortems</li>
                         <li>• Continuous improvement</li>
                         <li>• User communication</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="legal" title="Legal and Compliance">
                <div className="space-y-6">
                  <div className="p-6 rounded-2xl glass" style={{
                    backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                    border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                  }}>
                    <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                      Legal Position
                    </h3>
                    <ul className="space-y-2">
                      <li>• Not an ETF or registered security</li>
                      <li>• Counsel‑vetted positioning</li>
                      <li>• Distribution controls and restricted regions</li>
                      <li>• Optional path‑to‑regulation</li>
                    </ul>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                        Access Controls
                      </h3>
                      <ul className="space-y-2">
                        <li>• Geofencing and tiered primary access</li>
                        <li>• Sanctions screening</li>
                        <li>• Optional KYC/AML for primary market</li>
                        <li>• User responsibility for secondary</li>
                      </ul>
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                        Documentation
                      </h3>
                      <ul className="space-y-2">
                        <li>• Terms of Use</li>
                        <li>• Privacy Policy</li>
                        <li>• Risk Factors</li>
                        <li>• IP Policy</li>
                      </ul>
                    </div>
                  </div>
                </div>
                             </Section>

               <Section id="figures" title="Diagrams & Figures">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Mechanism Diagram
                       </h3>
                       <div className="bg-gray-100 dark:bg-gray-900 p-4 rounded-xl text-center" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         <div>Mint/Redeem ↔ Vault ↔ Treasury</div>
                         <div>↔ Oracles ↔ NAV</div>
                       </div>
                     </div>
                     <div className="p-6 rounded-2xl glass" style={{
                       backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                       border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                     }}>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Governance Flow
                       </h3>
                       <div className="bg-gray-100 dark:bg-gray-900 p-4 rounded-xl text-center" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         <div>Proposal → Vote → Timelock</div>
                         <div>→ Execution (bounded params)</div>
                       </div>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="api" title="Data & API">
                 <div className="space-y-6">
                   <p className="text-lg" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                     Public, rate‑limited endpoints and on‑chain views provide transparency without exposing proprietary parameters.
                   </p>
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       Example Endpoints
                     </h3>
                     <div className="bg-gray-100 dark:bg-gray-900 p-4 rounded-xl text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       <div>GET /api/v1/nav - NAV per share</div>
                       <div>GET /api/v1/holdings - Asset holdings</div>
                       <div>GET /api/v1/allocations - Weight allocations</div>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="stress" title="Stress Scenarios and Backtesting">
                 <div className="space-y-6">
                   <p className="text-lg" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                     Illustrative outcomes under historical drawdowns and liquidity shocks, net of transaction costs but before fees:
                   </p>
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                       <div>
                         <div className="text-lg font-bold mb-1" style={{ color: '#ef4444' }}>2018 Bear</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Passive: -72%</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Veriless: -55%</div>
                       </div>
                       <div>
                         <div className="text-lg font-bold mb-1" style={{ color: '#f97316' }}>Mar-2020</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Passive: -55%</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Veriless: -42%</div>
                       </div>
                       <div>
                         <div className="text-lg font-bold mb-1" style={{ color: '#eab308' }}>FTX 2022</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Passive: -25%</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Veriless: -18%</div>
                       </div>
                       <div>
                         <div className="text-lg font-bold mb-1" style={{ color: '#22c55e' }}>2024 ETF</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Passive: +45%</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>Veriless: +49%</div>
                       </div>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="bounty" title="Bug Bounty Program">
                 <div className="space-y-6">
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                       <div>
                         <div className="text-lg font-bold mb-1" style={{ color: '#ef4444' }}>Critical</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>$50K–$250K</div>
                       </div>
                       <div>
                         <div className="text-lg font-bold mb-1" style={{ color: '#f97316' }}>High</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>$10K–$50K</div>
                       </div>
                       <div>
                         <div className="text-lg font-bold mb-1" style={{ color: '#eab308' }}>Medium</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>$2K–$10K</div>
                       </div>
                       <div>
                         <div className="text-lg font-bold mb-1" style={{ color: '#22c55e' }}>Low</div>
                         <div className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>$200–$2K</div>
                       </div>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="interfaces" title="Smart Contract Interfaces">
                 <div className="space-y-6">
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       Core Interfaces (Excerpt)
                     </h3>
                     <div className="bg-gray-100 dark:bg-gray-900 p-4 rounded-xl text-sm font-mono" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       <div>IVerilessVault: navPerShare, totalAssets</div>
                       <div>IConfigRegistry: getUint, setUint</div>
                       <div>IProofOfReserves: currentRoot, publishRoot</div>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="appendix-a" title="Appendix A: Methodology Notes">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Regression Bands
                       </h3>
                       <ul className="space-y-2">
                         <li>• Fit smooth trend to log price</li>
                         <li>• Estimate dispersion robustly</li>
                         <li>• Define buy/sell thresholds</li>
                         <li>• Position sizing with limits</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Backtesting Protocol
                       </h3>
                       <ul className="space-y-2">
                         <li>• Exchange‑agnostic prices</li>
                         <li>• Realistic cost modeling</li>
                         <li>• Train/test validation</li>
                         <li>• Comprehensive reporting</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="appendix-b" title="Appendix B: KPI Definitions">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Performance Metrics
                       </h3>
                       <ul className="space-y-2">
                         <li>• Alpha/Beta vs passive basket</li>
                         <li>• Sharpe/Sortino ratios</li>
                         <li>• Max drawdown</li>
                         <li>• Time under water</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Operational KPIs
                       </h3>
                       <ul className="space-y-2">
                         <li>• Turnover and capacity use</li>
                         <li>• Premium/discount volatility</li>
                         <li>• Tracking error</li>
                         <li>• Hit rate</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="appendix-c" title="Appendix C: Glossary">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Key Terms
                       </h3>
                       <ul className="space-y-2">
                         <li>• NAV: Net Asset Value per token</li>
                         <li>• Premium/Discount: Price vs NAV</li>
                         <li>• Regression Bands: Statistical bands</li>
                         <li>• Hysteresis: Non‑symmetric thresholds</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Technical Concepts
                       </h3>
                       <ul className="space-y-2">
                         <li>• Commit‑Reveal: Trade execution</li>
                         <li>• TWAP: Time‑weighted average price</li>
                         <li>• MPC: Multi‑party computation</li>
                         <li>• MEV: Maximal extractable value</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="risks" title="Risk Factors">
                 <div className="space-y-6">
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <p className="text-lg" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                       Digital assets are highly volatile; strategies may underperform passive exposure; smart contracts can fail; custody may be compromised; oracles can fail; regulatory actions can restrict access; liquidity may be insufficient during stress; fees reduce returns; historical results do not guarantee future performance.
                     </p>
                   </div>
                 </div>
               </Section>

               <Section id="notices" title="Legal Notices">
                 <div className="space-y-6">
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <p className="text-lg" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                       This document is for informational purposes only and does not constitute investment advice, an offer to sell, or a solicitation of an offer to buy any token or other financial instruments. Veriless is not an ETF or a registered security. Participation may be limited or prohibited by law in certain jurisdictions. Readers should seek independent legal, tax, and financial advice.
                     </p>
                   </div>
                 </div>
               </Section>

               <Section id="team" title="Team & Credits">
                 <div className="space-y-6">
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <p className="text-lg" style={{ color: isDark ? '#e0e0e0' : '#666666' }}>
                       Disclose core contributors, roles, and relevant experience (quant research, smart contracts, security, legal). Include conflict‑of‑interest statements and independent advisor bios.
                     </p>
                   </div>
                 </div>
               </Section>

               <Section id="accessibility" title="Accessibility">
                 <div className="space-y-6">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         Design Standards
                       </h3>
                       <ul className="space-y-2">
                         <li>• Color‑contrast compliant</li>
                         <li>• Keyboard‑navigable TOC</li>
                         <li>• ARIA labels on landmarks</li>
                         <li>• Skip‑to‑content support</li>
                       </ul>
                     </div>
                     <div>
                       <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                         User Experience
                       </h3>
                       <ul className="space-y-2">
                         <li>• Print‑friendly styles</li>
                         <li>• Responsive mobile layout</li>
                         <li>• Screen reader compatible</li>
                         <li>• High contrast options</li>
                       </ul>
                     </div>
                   </div>
                 </div>
               </Section>

               <Section id="changelog" title="Changelog and Versioning">
                 <div className="space-y-6">
                   <div className="p-6 rounded-2xl glass" style={{
                     backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                     border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)'
                   }}>
                     <h3 className="text-xl font-semibold mb-4" style={{ color: isDark ? '#ffffff' : '#000000' }}>
                       Version History
                     </h3>
                     <ul className="space-y-2">
                       <li><strong>v0.9</strong> (2025‑08‑12): Initial comprehensive draft with all sections</li>
                       <li>Semantic versioning: breaking changes bump major</li>
                       <li>New sections/features bump minor</li>
                       <li>Fixes/typos bump patch</li>
                     </ul>
                   </div>
                 </div>
               </Section>
             </div>
           </div>
         </div>
       </div>

      {/* Footer */}
      <div className="mt-20 px-6 py-12 border-t" style={{
        borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
      }}>
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-sm" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
            © 2025 Veriless Foundation. All rights reserved.
          </p>
          <p className="text-sm mt-2" style={{ color: isDark ? '#a0a0a0' : '#666666' }}>
            This is a living document. See repository history for changelog and prior versions.
          </p>
        </div>
      </div>
    </div>
  );
}
