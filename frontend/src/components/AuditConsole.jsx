import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import { 
  Play, 
  CheckCircle2, 
  FileText, 
  Download, 
  Cpu, 
  Calculator,
  Search,
  BookOpen,
  DollarSign,
  ArrowRight
} from 'lucide-react';
import gsap from 'gsap';
import { runAgenticAudit } from '../api';

export default function AuditConsole({ 
  countries = [], 
  products = [], 
  onAuditStart, 
  onAuditComplete,
  sourceCountry = 'United States',
  destinationCountry = 'India',
  onSourceChange,
  onDestinationChange
}) {
  const [formData, setFormData] = useState({
    product_name: 'Laptop',
    source_country: sourceCountry,
    destination: destinationCountry,
    price: 800,
    quantity: 2,
    shipping: 100
  });

  const [loading, setLoading] = useState(false);
  const [auditResult, setAuditResult] = useState(null);
  const [productSearch, setProductSearch] = useState('');
  const [showProductDropdown, setShowProductDropdown] = useState(false);
  // Portal dropdown: stores the pixel position of the input so the dropdown
  // can be rendered at body level (escaping any ancestor overflow:hidden)
  const [dropdownRect, setDropdownRect] = useState(null);
  const productInputRef = useRef(null);

  // GSAP animation refs
  const formCardRef = useRef(null);
  const resultsCardRef = useRef(null);
  const landedCostNumRef = useRef(null);
  const stepsContainerRef = useRef(null);
  const costTableRef = useRef(null);
  const submitBtnRef = useRef(null);

  // Sync with props
  useEffect(() => {
    setFormData(prev => ({
      ...prev,
      source_country: sourceCountry,
      destination: destinationCountry
    }));
  }, [sourceCountry, destinationCountry]);

  // Initial Entrance Animation with GSAP
  useEffect(() => {
    if (formCardRef.current) {
      const elements = formCardRef.current.querySelectorAll('.form-group, .form-row, .btn-primary');
      gsap.fromTo(
        elements,
        { opacity: 0, y: 16 },
        { opacity: 1, y: 0, duration: 0.5, stagger: 0.07, ease: 'power2.out' }
      );
    }
  }, []);

  // GSAP Animation when Audit Results Arrive
  useEffect(() => {
    if (auditResult && resultsCardRef.current) {
      // Fade in results container
      gsap.fromTo(
        resultsCardRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }
      );

      // Stagger cost table rows
      if (costTableRef.current) {
        const rows = costTableRef.current.querySelectorAll('tr');
        gsap.fromTo(
          rows,
          { opacity: 0, x: -12 },
          { opacity: 1, x: 0, duration: 0.35, stagger: 0.05, ease: 'power1.out' }
        );
      }

      // Stagger pipeline steps
      if (stepsContainerRef.current) {
        const stepElements = stepsContainerRef.current.querySelectorAll('.agent-step');
        gsap.fromTo(
          stepElements,
          { opacity: 0, x: 16 },
          { opacity: 1, x: 0, duration: 0.4, stagger: 0.08, ease: 'power2.out' }
        );
      }

      // Smooth numeric counter animation for Landed Cost
      if (landedCostNumRef.current) {
        const targetVal = auditResult.landing_cost;
        const counterObj = { val: 0 };
        gsap.to(counterObj, {
          val: targetVal,
          duration: 1.1,
          ease: 'power2.out',
          onUpdate: () => {
            if (landedCostNumRef.current) {
              landedCostNumRef.current.textContent = '$' + counterObj.val.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
              });
            }
          }
        });
      }
    }
  }, [auditResult]);

  // GSAP Hover Micro-Interactions
  const handleBtnMouseEnter = () => {
    if (submitBtnRef.current && !loading) {
      gsap.to(submitBtnRef.current, { scale: 1.02, duration: 0.2, ease: 'power1.out' });
    }
  };

  const handleBtnMouseLeave = () => {
    if (submitBtnRef.current) {
      gsap.to(submitBtnRef.current, { scale: 1, duration: 0.2, ease: 'power1.out' });
    }
  };

  const filteredProducts = products.filter(p => 
    p.Product.toLowerCase().includes(productSearch.toLowerCase()) ||
    p.HS_Code.toLowerCase().includes(productSearch.toLowerCase())
  ).slice(0, 8);

  const handleRunAudit = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    if (onAuditStart) onAuditStart(formData);

    try {
      const result = await runAgenticAudit(formData);
      setAuditResult(result);
      if (onAuditComplete) onAuditComplete(result);
    } catch (err) {
      alert('Audit failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = () => {
    if (!auditResult) return;
    const blob = new Blob([JSON.stringify(auditResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tax_audit_${auditResult.audit_id || 'report'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="workstation-grid">
        {/* LEFT COLUMN: Input Audit Specification */}
        <div className="card" ref={formCardRef}>
          <div className="card-header">
            <span className="card-title">
              <Calculator size={16} style={{ color: '#60a5fa' }} />
              Cross-Border Trade & Tariff Specification
            </span>
            <span className="brand-badge mono">INPUT_AGENT</span>
          </div>

          <div className="card-body">
            <form onSubmit={handleRunAudit}>
              {/* Product Selector with Live Autocomplete — dropdown via Portal */}
              <div className="form-group">
                <label className="form-label">Commercial Product Name</label>
                <input
                  ref={productInputRef}
                  type="text"
                  className="form-input"
                  value={formData.product_name}
                  onChange={(e) => {
                    setFormData({ ...formData, product_name: e.target.value });
                    setProductSearch(e.target.value);
                    setShowProductDropdown(true);
                    // Measure the input so we can position the portal dropdown
                    if (productInputRef.current) {
                      const r = productInputRef.current.getBoundingClientRect();
                      setDropdownRect({ top: r.bottom + window.scrollY + 4, left: r.left + window.scrollX, width: r.width });
                    }
                  }}
                  onFocus={() => {
                    setShowProductDropdown(true);
                    if (productInputRef.current) {
                      const r = productInputRef.current.getBoundingClientRect();
                      setDropdownRect({ top: r.bottom + window.scrollY + 4, left: r.left + window.scrollX, width: r.width });
                    }
                  }}
                  onBlur={() => setTimeout(() => setShowProductDropdown(false), 150)}
                  placeholder="e.g. Laptop, Industrial Valve, Chemical..."
                  required
                />
              </div>

              {/* Portal dropdown — renders at <body> to escape card's overflow:hidden */}
              {showProductDropdown && productSearch && filteredProducts.length > 0 && dropdownRect &&
                ReactDOM.createPortal(
                  <div
                    className="product-dropdown-menu"
                    style={{
                      position: 'absolute',
                      top: dropdownRect.top,
                      left: dropdownRect.left,
                      width: dropdownRect.width,
                    }}
                  >
                    {filteredProducts.map((p) => (
                      <div
                        key={p.Product_ID || p.Product}
                        className="product-dropdown-item"
                        onMouseDown={() => {
                          setFormData({ ...formData, product_name: p.Product });
                          setProductSearch(p.Product);
                          setShowProductDropdown(false);
                        }}
                      >
                        <span style={{ fontWeight: 500 }}>{p.Product}</span>
                        <span className="product-dropdown-badge">HS {p.HS_Code}</span>
                      </div>
                    ))}
                  </div>,
                  document.body
                )
              }

              {/* Source (Origin) Country Input */}
              <div className="form-group">
                <label className="form-label">Source Country (Export Origin Port)</label>
                <select
                  className="form-select"
                  value={formData.source_country}
                  onChange={(e) => {
                    const val = e.target.value;
                    setFormData({ ...formData, source_country: val });
                    if (onSourceChange) onSourceChange(val);
                  }}
                >
                  {countries.map((c) => (
                    <option key={`src-${c.Country}`} value={c.Country}>
                      {c.Country} ({c.Currency})
                    </option>
                  ))}
                </select>
              </div>

              {/* Destination Country Input */}
              <div className="form-group">
                <label className="form-label">Destination Country (Customs Import Port)</label>
                <select
                  className="form-select"
                  value={formData.destination}
                  onChange={(e) => {
                    const val = e.target.value;
                    setFormData({ ...formData, destination: val });
                    if (onDestinationChange) onDestinationChange(val);
                  }}
                >
                  {countries.map((c) => (
                    <option key={`dest-${c.Country}`} value={c.Country}>
                      {c.Country} ({c.Currency}) — Tariff: {c.Default_Import_Duty_Percent}% | VAT: {c.GST_VAT_Percent}%
                    </option>
                  ))}
                </select>
              </div>

              {/* Unit Price & Quantity */}
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Unit Price (USD)</label>
                  <input
                    type="number"
                    step="any"
                    min="0.01"
                    className="form-input mono"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    className="form-input mono"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    required
                  />
                </div>
              </div>

              {/* Shipping Freight Cost (Insurance Removed) */}
              <div className="form-group">
                <label className="form-label">Shipping Freight Cost (USD)</label>
                <input
                  type="number"
                  step="any"
                  min="0"
                  className="form-input mono"
                  value={formData.shipping}
                  onChange={(e) => setFormData({ ...formData, shipping: e.target.value })}
                  required
                />
              </div>

              {/* Action Button (Compare button removed per user request) */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 24 }}>
                <button 
                  type="submit" 
                  className="btn-primary" 
                  disabled={loading}
                  ref={submitBtnRef}
                  onMouseEnter={handleBtnMouseEnter}
                  onMouseLeave={handleBtnMouseLeave}
                >
                  <Play size={14} />
                  {loading ? 'Executing Multi-Agent Pipeline...' : 'Run Autonomous Tax Audit'}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* RIGHT COLUMN: Live Execution & Audit Findings */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {auditResult ? (
            <div ref={resultsCardRef} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Executive Summary Verdict Header */}
              <div className="card" style={{ borderLeft: '4px solid #10b981' }}>
                <div className="card-body" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="badge badge-success">
                        <CheckCircle2 size={12} />
                        PIPELINE COMPLETED
                      </span>
                      <span className="mono" style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        ID: {auditResult.audit_id}
                      </span>
                      <span className="mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                        {auditResult.timestamp}
                      </span>
                    </div>

                    <div style={{ marginTop: 6, fontSize: 13, color: 'var(--text-muted)' }}>
                      Corridor: <strong style={{ color: 'var(--text-main)' }}>{formData.source_country}</strong> &rarr; <strong style={{ color: 'var(--text-main)' }}>{auditResult.destination}</strong>
                    </div>

                    <h2 style={{ fontSize: 22, marginTop: 6, fontWeight: 600 }}>
                      Final Landed Cost: <span className="mono" ref={landedCostNumRef} style={{ color: 'var(--text-main)' }}>${auditResult.landing_cost?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                    </h2>
                    <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
                      Local Equivalent: <span className="mono" style={{ color: '#3b82f6' }}>{auditResult.currency} {auditResult.local_landing_cost?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                      {' • '}Effective Tax Burden: <span className="mono">{auditResult.effective_tax_rate}%</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn-secondary" onClick={handleDownloadReport}>
                      <Download size={13} />
                      Export Certificate (JSON)
                    </button>
                    <button className="btn-secondary" onClick={() => window.print()}>
                      <FileText size={13} />
                      Print Summary
                    </button>
                  </div>
                </div>
              </div>

              {/* Two Panel Grid: Cost Breakdown & RAG Regulatory Notes */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
                {/* Financial Customs Sheet */}
                <div className="card">
                  <div className="card-header">
                    <span className="card-title">
                      <DollarSign size={15} style={{ color: '#10b981' }} />
                      Customs Valuation & Duty Schedule
                    </span>
                    <span className="brand-badge mono">CALC_AGENT</span>
                  </div>
                  <div className="card-body">
                    <table className="cost-table" ref={costTableRef}>
                      <tbody>
                        <tr>
                          <td style={{ color: 'var(--text-muted)' }}>Commercial Product Cost</td>
                          <td>${auditResult.product_cost?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        </tr>
                        <tr>
                          <td style={{ color: 'var(--text-muted)' }}>Shipping Freight Cost</td>
                          <td>${Number(formData.shipping).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        </tr>
                        <tr>
                          <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>Assessable Customs Value</td>
                          <td style={{ fontWeight: 600 }}>${auditResult.customs_value?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        </tr>
                        <tr>
                          <td style={{ color: 'var(--text-muted)' }}>Customs Import Duty ({auditResult.duty_rate}%)</td>
                          <td style={{ color: '#f59e0b' }}>+ ${auditResult.customs_duty?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        </tr>
                        <tr>
                          <td style={{ color: 'var(--text-muted)' }}>Statutory Taxable Value</td>
                          <td>${auditResult.taxable_value?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        </tr>
                        <tr>
                          <td style={{ color: 'var(--text-muted)' }}>GST / VAT ({auditResult.gst_rate}%)</td>
                          <td style={{ color: '#f59e0b' }}>+ ${auditResult.gst_vat?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        </tr>
                        <tr className="total-row">
                          <td>Total Landed Cost</td>
                          <td style={{ color: '#10b981' }}>${auditResult.landing_cost?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        </tr>
                      </tbody>
                    </table>

                    <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-dim)' }}>
                      <span>Unit Landed: <strong className="mono" style={{ color: 'var(--text-main)' }}>${auditResult.landed_cost_per_unit}/unit</strong></span>
                      <span>Unit Tax Duty: <strong className="mono" style={{ color: 'var(--text-main)' }}>${auditResult.tax_burden_per_unit}/unit</strong></span>
                    </div>
                  </div>
                </div>

                {/* RAG Policy & Regulatory Compliance */}
                <div className="card">
                  <div className="card-header">
                    <span className="card-title">
                      <BookOpen size={15} style={{ color: '#3b82f6' }} />
                      RAG Trade Policy & Regulatory Evidence
                    </span>
                    <span className="brand-badge mono">RAG_POLICY_AGENT</span>
                  </div>
                  <div className="card-body">
                    <div style={{ marginBottom: 12 }}>
                      <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: 4 }}>
                        Product Classification
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontWeight: 600 }}>{auditResult.product}</span>
                        <span className="mono" style={{ padding: '2px 6px', background: 'var(--bg-hover)', borderRadius: 4, fontSize: 11 }}>
                          HS {auditResult.hs_code}
                        </span>
                        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>({auditResult.category})</span>
                      </div>
                    </div>

                    <div style={{ marginBottom: 12 }}>
                      <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: 4 }}>
                        Active Trade Policy Clause
                      </div>
                      <div style={{ fontSize: 13, color: 'var(--text-main)', background: 'var(--bg-main)', padding: 10, borderRadius: 6, border: '1px solid var(--border)' }}>
                        {auditResult.policy}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: 4 }}>
                        Compliance Note & Clearance Directives
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', background: 'var(--bg-main)', padding: 10, borderRadius: 6, border: '1px solid var(--border)' }}>
                        {auditResult.compliance}
                      </div>
                    </div>

                    <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 11, color: 'var(--text-dim)' }}>
                      <span>Source: {auditResult.source_type}</span>
                      <span className="badge">Prototype policy record</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Multi-Agent Provenance Trace with GSAP Stagger */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title">
                    <Cpu size={15} style={{ color: '#3b82f6' }} />
                    Autonomous Agent Execution Pipeline Trace
                  </span>
                  <span className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    Total Latency: {auditResult.total_pipeline_latency_ms} ms
                  </span>
                </div>
                <div className="card-body">
                  <div className="agent-pipeline" ref={stepsContainerRef}>
                    {auditResult.execution_steps?.map((step) => (
                      <div key={step.step} className="agent-step">
                        <div className="agent-num">{step.step}</div>
                        <div className="agent-step-info">
                          <div className="agent-step-header">
                            <span className="agent-name">{step.agent}</span>
                            <span className="agent-latency mono">{step.latency}</span>
                          </div>
                          <div className="agent-desc">{step.description}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="card" style={{ padding: 48, textAlign: 'center' }}>
              <div style={{ maxWidth: 460, margin: '0 auto' }}>
                <div style={{ width: 44, height: 44, borderRadius: 8, background: 'var(--bg-card)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px', color: '#3b82f6', border: '1px solid var(--border)' }}>
                  <Play size={20} />
                </div>
                <h3 style={{ fontSize: 16, marginBottom: 8 }}>Auditor Standby</h3>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                  Select Source Country (Origin) and Destination Country, enter commercial product specs, and click <strong>Run Autonomous Tax Audit</strong> to initiate the 6-agent verification pipeline.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
