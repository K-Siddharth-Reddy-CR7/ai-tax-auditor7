import React, { useEffect, useRef } from 'react';
import { Check, X, Shield, Cpu, Zap, Activity } from 'lucide-react';
import gsap from 'gsap';

// Descriptive checklist of processing steps implemented in backend/server.py.
// This is NOT a measured result. Measured accuracy, abstention and silent-error rates are
// produced only by the reproducible study in research_paper/experiments/.
const BENCHMARK_DATA = [
  {
    feature: 'Product Identification',
    normal: true,
    agentic: true,
    description: 'Catalogue lookup over 1,200 synthetic product records. Baseline: substring match. Staged pipeline: exact/prefix, substring and word-overlap match, with a fixed fallback HS code when nothing matches.'
  },
  {
    feature: 'Tax & Landed-Cost Calculation',
    normal: true,
    agentic: true,
    description: 'Country-level duty and VAT/GST rates from a 40-country prototype table; landed cost = (unit price x quantity + freight) x (1 + duty) x (1 + VAT).'
  },
  {
    feature: 'Policy Lookup',
    normal: false,
    agentic: true,
    description: 'Lexical TF-IDF retrieval over 240 prototype policy records (placeholder text). No text generation.'
  },
  {
    feature: 'Sequential Processing Stages',
    normal: false,
    agentic: true,
    description: 'Six sequential Python functions (input, product, policy, tax, calculation, report) that pass one shared record.'
  },
  {
    feature: 'Keyword Policy Flag',
    normal: false,
    agentic: true,
    description: 'Keyword rule on the retrieved policy text (cleared / permit required / prohibited). With the current placeholder policies it always returns "cleared".'
  },
  {
    feature: 'Execution Trace',
    normal: false,
    agentic: true,
    description: 'Per-stage latency log, timestamp and a time-based audit ID.'
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
      {/* Overview Cards: descriptive only (hard-coded performance figures removed) */}
      <div className="kpi-row" ref={kpiRef}>
        <div className="kpi-card">
          <div className="kpi-label">
            What this page shows
            <Shield size={14} style={{ color: '#38bdf8' }} />
          </div>
          <div className="kpi-sub">
            A descriptive checklist of the processing steps each pipeline implements, taken from the
            source code. It is not an accuracy, recall or false-negative measurement.
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">
            Measured evaluation
            <Activity size={14} style={{ color: '#60a5fa' }} />
          </div>
          <div className="kpi-sub">
            Accuracy, abstention and silent-error rates are measured in a separate, reproducible study
            (research_paper/experiments). No measured values are shown on this page.
          </div>
        </div>
      </div>

      {/* Implemented-steps checklist (yes/no; not a measurement) */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">
            <Activity size={15} style={{ color: '#60a5fa' }} />
            Implemented Processing Steps (from source code)
          </span>
          <span className="mono" style={{ fontSize: 11, color: '#94a3b8' }}>DESCRIPTIVE - NOT A MEASUREMENT</span>
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
                      {item.normal ? 'Baseline' : '—'}
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
                      Staged
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 24, justifyContent: 'flex-end', marginTop: 20, paddingTop: 16, borderTop: '1px solid #232938', fontSize: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: '#334155' }} />
              <span style={{ color: '#94a3b8' }}>Single-pass baseline</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: '#10b981' }} />
              <span style={{ color: '#e2e8f0' }}>Staged pipeline</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Deep Dive Table */}
      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Processing step</th>
              <th>Single-pass baseline</th>
              <th>Staged pipeline</th>
              <th>Implementation (backend/server.py)</th>
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
                      <Check size={11} /> Implemented
                    </span>
                  ) : (
                    <span style={{ color: '#64748b', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
                      <X size={11} /> Not implemented
                    </span>
                  )}
                </td>
                <td>
                  <span className="badge badge-success">
                    <Check size={11} /> Implemented
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
