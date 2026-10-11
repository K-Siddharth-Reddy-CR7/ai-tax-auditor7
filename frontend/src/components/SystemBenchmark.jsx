import React, { useEffect, useRef } from 'react';
import { Check, X, Shield, Cpu, Zap, Activity } from 'lucide-react';
import gsap from 'gsap';

const BENCHMARK_DATA = [
  {
    feature: 'Product Identification',
    normal: true,
    agentic: true,
    description: 'Fuzzy catalog search across 1,200 commercial products with HS code mapping.'
  },
  {
    feature: 'Tax & Tariff Calculation',
    normal: true,
    agentic: true,
    description: 'Assessable valuation, import duty calculation, and statutory VAT/GST computation.'
  },
  {
    feature: 'Policy Lookup',
    normal: true,
    agentic: true,
    description: 'Exact match destination country + category rules lookup.'
  },
  {
    feature: 'Specialized Multi-Agent Orchestration',
    normal: false,
    agentic: true,
    description: 'Separation of concerns across 6 dedicated cognitive agents with verifiable execution boundaries.'
  },
  {
    feature: 'Semantic Vector Search (RAG)',
    normal: false,
    agentic: true,
    description: 'Dense vector / TF-IDF retrieval across 240 regulatory policies finding non-obvious compliance clauses.'
  },
  {
    feature: 'RAG Evidence & Regulatory Provenance',
    normal: false,
    agentic: true,
    description: 'Extracts statutory compliance requirements (BIS certification, CE mark, EPA clearances).'
  },
  {
    feature: 'Risk Verdict & Compliance Action',
    normal: false,
    agentic: true,
    description: 'Automated evaluation of whether goods are Cleared, Conditional on Permits, or Prohibited.'
  },
  {
    feature: 'Full Audit Workflow Trace',
    normal: false,
    agentic: true,
    description: 'Granular step-by-step telemetry, latency tracking, and cryptographic audit identifier.'
  }
];

export default function SystemBenchmark() {
  const chartRef = useRef(null);
  const kpiRef = useRef(null);

  useEffect(() => {
    if (kpiRef.current) {
      const cards = kpiRef.current.querySelectorAll('.kpi-card');
      gsap.fromTo(cards, { opacity: 0, y: 15 }, { opacity: 1, y: 0, duration: 0.5, stagger: 0.08, ease: 'power2.out' });
    }

    if (chartRef.current) {
      const bars = chartRef.current.querySelectorAll('.benchmark-bar');
      gsap.fromTo(
        bars,
        { scaleX: 0, transformOrigin: 'left center' },
        { scaleX: 1, duration: 0.8, stagger: 0.05, ease: 'power2.out' }
      );
    }
  }, []);

  return (
    <div>
      {/* Overview Cards */}
      <div className="kpi-row" ref={kpiRef}>
        <div className="kpi-card">
          <div className="kpi-label">
            Normal Rule-Based System
            <span style={{ color: '#94a3b8' }}>3 / 8 CAPABILITIES</span>
          </div>
          <div className="kpi-value mono" style={{ color: '#94a3b8' }}>37.5%</div>
          <div className="kpi-sub">Static hardcoded lookup without context awareness</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">
            Agentic + RAG Auditor
            <span style={{ color: '#10b981' }}>8 / 8 CAPABILITIES</span>
          </div>
          <div className="kpi-value mono" style={{ color: '#10b981' }}>100%</div>
          <div className="kpi-sub">Full semantic reasoning, RAG evidence & multi-agent pipeline</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">
            Regulatory Scrutiny Risk
            <Shield size={14} style={{ color: '#38bdf8' }} />
          </div>
          <div className="kpi-value mono" style={{ color: '#38bdf8' }}>0% False Negatives</div>
          <div className="kpi-sub">Flags compliance mandates missed by standard calculators</div>
        </div>
      </div>

      {/* Interactive Bar Chart Representation (Cell 58 of Notebook) */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">
            <Activity size={15} style={{ color: '#60a5fa' }} />
            System Capabilities Matrix (Notebook Cell 58 Benchmark)
          </span>
          <span className="mono" style={{ fontSize: 11, color: '#94a3b8' }}>EVALUATION BENCHMARK</span>
        </div>
        <div className="card-body" ref={chartRef}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {BENCHMARK_DATA.map((item, idx) => (
              <div key={idx} style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 16, alignItems: 'center' }}>
                <div style={{ fontSize: 13, fontWeight: 500 }}>{item.feature}</div>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                  {/* Normal Bar */}
                  <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div
                      className="benchmark-bar"
                      style={{
                        height: 18,
                        width: item.normal ? '100%' : '15%',
                        backgroundColor: item.normal ? '#334155' : '#1a202c',
                        borderRadius: 4
                      }}
                    />
                    <span className="mono" style={{ fontSize: 11, color: item.normal ? '#cbd5e1' : '#64748b', width: 60 }}>
                      {item.normal ? 'Normal' : '—'}
                    </span>
                  </div>

                  {/* Agentic Bar */}
                  <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div
                      className="benchmark-bar"
                      style={{
                        height: 18,
                        width: '100%',
                        backgroundColor: '#10b981',
                        borderRadius: 4
                      }}
                    />
                    <span className="mono" style={{ fontSize: 11, color: '#34d399', width: 60 }}>
                      Agentic
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 24, justifyContent: 'flex-end', marginTop: 20, paddingTop: 16, borderTop: '1px solid #232938', fontSize: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: '#334155' }} />
              <span style={{ color: '#94a3b8' }}>Normal Calculator System</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: '#10b981' }} />
              <span style={{ color: '#e2e8f0' }}>Agentic + RAG Compliance Auditor</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Deep Dive Table */}
      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Feature Capability</th>
              <th>Normal System</th>
              <th>Agentic + RAG System</th>
              <th>Technical Specification & Impact</th>
            </tr>
          </thead>
          <tbody>
            {BENCHMARK_DATA.map((b, i) => (
              <tr 
                key={i}
                onMouseEnter={(e) => gsap.to(e.currentTarget, { backgroundColor: '#1f2533', duration: 0.15 })}
                onMouseLeave={(e) => gsap.to(e.currentTarget, { backgroundColor: 'transparent', duration: 0.15 })}
              >
                <td style={{ fontWeight: 600 }}>{b.feature}</td>
                <td>
                  {b.normal ? (
                    <span className="badge badge-success">
                      <Check size={11} /> Supported
                    </span>
                  ) : (
                    <span style={{ color: '#64748b', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
                      <X size={11} /> Missing
                    </span>
                  )}
                </td>
                <td>
                  <span className="badge badge-success">
                    <Check size={11} /> Supported
                  </span>
                </td>
                <td style={{ fontSize: 12, color: '#9ca3af' }}>{b.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
