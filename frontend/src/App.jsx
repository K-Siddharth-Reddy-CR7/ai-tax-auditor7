import React, { useState, useEffect, useRef } from 'react';
import { 
  ShieldCheck, 
  Globe, 
  Calculator, 
  Layers, 
  BookOpen, 
  BarChart3, 
  Box,
  Sun,
  Moon
} from 'lucide-react';
import gsap from 'gsap';
import { fetchHealth, fetchStats, fetchCountries, fetchProducts } from './api';
import AuditConsole from './components/AuditConsole';
import ThreeCanvas from './components/ThreeCanvas';
import BatchAuditor from './components/BatchAuditor';
import PolicyExplorer from './components/PolicyExplorer';
import SystemBenchmark from './components/SystemBenchmark';

export default function App() {
  const [activeTab, setActiveTab] = useState('audit'); // 'audit' | '3d-flow' | 'batch' | 'policies' | 'benchmark'
  const [backendHealth, setBackendHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [countries, setCountries] = useState([]);
  const [products, setProducts] = useState([]);
  const [sourceCountry, setSourceCountry] = useState('United States');
  const [activeDestination, setActiveDestination] = useState('India');
  const [activeProduct, setActiveProduct] = useState('Laptop');
  const [isAuditing, setIsAuditing] = useState(false);

  const mainContentRef = useRef(null);
  const kpiRowRef = useRef(null);
  const headerRef = useRef(null);

  // Apply data-theme attribute on document root
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Initial data fetch & GSAP entrance timeline
  useEffect(() => {
    const initData = async () => {
      try {
        const health = await fetchHealth();
        setBackendHealth(health);
      } catch (e) {
        setBackendHealth({ status: 'offline' });
      }

      try {
        const s = await fetchStats();
        setStats(s);
      } catch (e) {}

      try {
        const c = await fetchCountries();
        setCountries(c.countries || []);
      } catch (e) {}

      try {
        const p = await fetchProducts('', 200);
        setProducts(p.items || []);
      } catch (e) {}
    };

    initData();

    // GSAP page load entrance animation
    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
    if (headerRef.current) {
      tl.fromTo(headerRef.current, { y: -30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6 });
    }
    if (kpiRowRef.current) {
      const cards = kpiRowRef.current.querySelectorAll('.kpi-card');
      tl.fromTo(cards, { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, stagger: 0.08 }, '-=0.3');
    }
  }, []);

  // GSAP tab switch animation
  const handleTabChange = (newTab) => {
    if (newTab === activeTab) return;
    if (mainContentRef.current) {
      gsap.to(mainContentRef.current, {
        opacity: 0,
        y: 8,
        duration: 0.16,
        ease: 'power1.in',
        onComplete: () => {
          setActiveTab(newTab);
          gsap.fromTo(
            mainContentRef.current,
            { opacity: 0, y: 12 },
            { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out' }
          );
        }
      });
    } else {
      setActiveTab(newTab);
    }
  };

  const handleAuditStart = (data) => {
    setIsAuditing(true);
    if (data.source_country) setSourceCountry(data.source_country);
    if (data.destination) setActiveDestination(data.destination);
    if (data.product_name) setActiveProduct(data.product_name);
  };

  const handleAuditComplete = (result) => {
    setIsAuditing(false);
    if (result && result.destination) {
      setActiveDestination(result.destination);
    }
  };

  return (
    <div className="app-container">
      {/* Top Navigation Header */}
      <header className="top-header" ref={headerRef}>
        <div className="header-brand">
          <div className="brand-icon">
            <ShieldCheck size={18} />
          </div>
          <div>
            <div className="brand-title">
              LEXITAX AUDIT
              <span className="brand-badge">Multi-Agent RAG</span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => handleTabChange('audit')}
          >
            <Calculator size={14} />
            Audit Workstation
          </button>
          <button
            className={`nav-tab ${activeTab === '3d-flow' ? 'active' : ''}`}
            onClick={() => handleTabChange('3d-flow')}
          >
            <Globe size={14} />
            3D Geographical Globe
          </button>
          <button
            className={`nav-tab ${activeTab === 'batch' ? 'active' : ''}`}
            onClick={() => handleTabChange('batch')}
          >
            <Layers size={14} />
            Batch Auditor (400)
          </button>
          <button
            className={`nav-tab ${activeTab === 'policies' ? 'active' : ''}`}
            onClick={() => handleTabChange('policies')}
          >
            <BookOpen size={14} />
            Trade Policies (240)
          </button>
          <button
            className={`nav-tab ${activeTab === 'benchmark' ? 'active' : ''}`}
            onClick={() => handleTabChange('benchmark')}
          >
            <BarChart3 size={14} />
            System Benchmark
          </button>
        </nav>

        {/* Right Header Status & Black/White Theme Toggle */}
        <div className="header-meta">
          {/* Black & White Theme Switcher */}
          <button 
            className="theme-toggle-btn"
            onClick={toggleTheme}
            title="Toggle Black / White Theme"
          >
            {theme === 'dark' ? (
              <>
                <Sun size={14} style={{ color: '#f59e0b' }} />
                <span>White Theme</span>
              </>
            ) : (
              <>
                <Moon size={14} style={{ color: '#3b82f6' }} />
                <span>Black Theme</span>
              </>
            )}
          </button>

          <div className="status-pill">
            <div className={`status-dot ${backendHealth?.status === 'healthy' ? '' : 'error'}`} />
            {backendHealth?.status === 'healthy' ? (
              <span>ONLINE // {stats ? `${stats.total_countries} COUNTRIES` : 'READY'}</span>
            ) : (
              <span style={{ color: '#ef4444' }}>BACKEND OFFLINE</span>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content" ref={mainContentRef}>
        {/* KPI Strip */}
        {stats && (
          <div className="kpi-row" ref={kpiRowRef} style={{ marginBottom: 20 }}>
            <div className="kpi-card">
              <div className="kpi-label">
                Cataloged Commodities
                <Box size={13} style={{ color: '#60a5fa' }} />
              </div>
              <div className="kpi-value mono">{stats.total_products?.toLocaleString()}</div>
              <div className="kpi-sub">Standardized HS-6 Classification Items</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">
                Customs Jurisdictions
                <Globe size={13} style={{ color: '#10b981' }} />
              </div>
              <div className="kpi-value mono">{stats.total_countries}</div>
              <div className="kpi-sub">Tariff schedules & VAT schedules indexed</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">
                Active Trade Policies
                <BookOpen size={13} style={{ color: '#f59e0b' }} />
              </div>
              <div className="kpi-value mono">{stats.total_policies}</div>
              <div className="kpi-sub">Indexed in vector RAG compliance database</div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">
                Mean Statutory Duty
                <span className="mono" style={{ color: 'var(--text-muted)' }}>% RATE</span>
              </div>
              <div className="kpi-value mono">{stats.average_duty_percent}%</div>
              <div className="kpi-sub">Average cross-border import tariff</div>
            </div>
          </div>
        )}

        {/* Tab 1: Single Audit Workstation */}
        {activeTab === 'audit' && (
          <div>
            <AuditConsole
              countries={countries}
              products={products}
              sourceCountry={sourceCountry}
              destinationCountry={activeDestination}
              onSourceChange={setSourceCountry}
              onDestinationChange={setActiveDestination}
              onAuditStart={handleAuditStart}
              onAuditComplete={handleAuditComplete}
            />

            {/* Live 3D Geographical Trade Corridor — full uncropped globe */}
            <div style={{ marginTop: 24 }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 12,
                flexWrap: 'wrap',
                gap: 8
              }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 600 }}>
                  <Globe size={15} style={{ color: '#3b82f6' }} />
                  Live 3D Geographical Trade Corridor:&nbsp;
                  <span style={{ color: '#3b82f6' }}>{sourceCountry}</span>
                  &nbsp;→&nbsp;
                  <span style={{ color: '#10b981' }}>{activeDestination}</span>
                </span>
                <button className="btn-secondary" onClick={() => handleTabChange('3d-flow')}>
                  <Globe size={13} />
                  Open Fullscreen Globe &amp; Pipeline
                </button>
              </div>
              <ThreeCanvas
                sourceCountry={sourceCountry}
                activeDestination={activeDestination}
                activeProduct={activeProduct}
                isAuditing={isAuditing}
                isDark={theme === 'dark'}
                onSelectHub={(country) => setActiveDestination(country)}
              />
            </div>
          </div>
        )}

        {/* Tab 2: Fullscreen 3D Geographical Trade Globe View */}
        {activeTab === '3d-flow' && (
          <div>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
              <div>
                <h2 style={{ fontSize: 18, fontWeight: 600 }}>Interactive 3D Geographical Map & Multi-Agent Network</h2>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
                  Equirectangular world continents, live cargo pulses, and descriptive multi-agent pipeline specification.
                </p>
              </div>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Source:</span>
                  <select
                    className="form-select"
                    style={{ width: 140 }}
                    value={sourceCountry}
                    onChange={(e) => setSourceCountry(e.target.value)}
                  >
                    {countries.map(c => (
                      <option key={`3d-src-${c.Country}`} value={c.Country}>{c.Country}</option>
                    ))}
                  </select>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Destination:</span>
                  <select
                    className="form-select"
                    style={{ width: 140 }}
                    value={activeDestination}
                    onChange={(e) => setActiveDestination(e.target.value)}
                  >
                    {countries.map(c => (
                      <option key={`3d-dest-${c.Country}`} value={c.Country}>{c.Country}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <ThreeCanvas 
              sourceCountry={sourceCountry}
              activeDestination={activeDestination}
              activeProduct={activeProduct}
              isAuditing={isAuditing}
              isDark={theme === 'dark'}
              onSelectHub={(country) => setActiveDestination(country)}
            />
          </div>
        )}

        {/* Tab 3: Batch Auditor */}
        {activeTab === 'batch' && <BatchAuditor />}

        {/* Tab 4: Policy Explorer */}
        {activeTab === 'policies' && <PolicyExplorer countries={countries} />}

        {/* Tab 5: System Benchmark */}
        {activeTab === 'benchmark' && <SystemBenchmark />}
      </main>
    </div>
  );
}
