import React, { useState, useEffect, useRef } from 'react';
import { Search, Filter, AlertCircle, CheckCircle2, RefreshCw, FileText, ArrowRight } from 'lucide-react';
import gsap from 'gsap';
import { fetchTransactions } from '../api';

export default function BatchAuditor() {
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [page, setPage] = useState(0);
  const limit = 25;
  const [selectedTx, setSelectedTx] = useState(null);

  const kpiRef = useRef(null);
  const tableRef = useRef(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchTransactions({
        limit,
        offset: page * limit,
        search,
        risk: riskFilter
      });
      setTransactions(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [page, search, riskFilter]);

  // GSAP animation for KPI row on mount
  useEffect(() => {
    if (kpiRef.current) {
      const cards = kpiRef.current.querySelectorAll('.kpi-card');
      gsap.fromTo(
        cards,
        { opacity: 0, y: 15 },
        { opacity: 1, y: 0, duration: 0.5, stagger: 0.08, ease: 'power2.out' }
      );
    }
  }, []);

  // GSAP animation for table rows on transactions update
  useEffect(() => {
    if (tableRef.current) {
      const rows = tableRef.current.querySelectorAll('tbody tr');
      gsap.fromTo(
        rows,
        { opacity: 0, y: 8 },
        { opacity: 1, y: 0, duration: 0.35, stagger: 0.025, ease: 'power1.out' }
      );
    }
  }, [transactions]);

  // Aggregate stats from transactions
  const totalVolume = transactions.reduce((acc, t) => acc + (t.Customs_Value_USD || 0), 0);
  const totalDuty = transactions.reduce((acc, t) => acc + (t.Duty_USD || 0), 0);
  const flaggedCount = transactions.filter(t => t.Audit_Status === 'FLAGGED').length;

  return (
    <div>
      {/* KPI Cards with GSAP ref */}
      <div className="kpi-row" ref={kpiRef}>
        <div className="kpi-card">
          <div className="kpi-label">
            Sample Transactions
            <FileText size={14} style={{ color: '#60a5fa' }} />
          </div>
          <div className="kpi-value mono">{total}</div>
          <div className="kpi-sub">Total records in dataset catalog</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">
            Current Batch Volume
            <span className="mono" style={{ color: '#10b981' }}>USD</span>
          </div>
          <div className="kpi-value mono">${totalVolume.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
          <div className="kpi-sub">Assessable freight value for current view</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">
            Assessed Duty
            <span className="mono" style={{ color: '#f59e0b' }}>TARIFF</span>
          </div>
          <div className="kpi-value mono">${totalDuty.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
          <div className="kpi-sub">Customs import duty revenue assessed</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">
            Flagged for Scrutiny
            <AlertCircle size={14} style={{ color: '#f59e0b' }} />
          </div>
          <div className="kpi-value mono" style={{ color: flaggedCount > 0 ? '#f59e0b' : '#10b981' }}>
            {flaggedCount} / {transactions.length}
          </div>
          <div className="kpi-sub">High customs valuation or elevated tariff</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-body" style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: 260 }}>
            <Search size={14} style={{ position: 'absolute', left: 12, top: 12, color: '#64748b' }} />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: 34 }}
              placeholder="Search product, HS code, origin or destination..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <button
              className={`btn-secondary ${riskFilter === '' ? 'active' : ''}`}
              onClick={() => { setRiskFilter(''); setPage(0); }}
            >
              All Records
            </button>
            <button
              className={`btn-secondary ${riskFilter === 'CLEARED' ? 'active' : ''}`}
              onClick={() => { setRiskFilter('CLEARED'); setPage(0); }}
            >
              <CheckCircle2 size={13} style={{ color: '#10b981' }} />
              Cleared
            </button>
            <button
              className={`btn-secondary ${riskFilter === 'FLAGGED' ? 'active' : ''}`}
              onClick={() => { setRiskFilter('FLAGGED'); setPage(0); }}
            >
              <AlertCircle size={13} style={{ color: '#f59e0b' }} />
              Flagged Scrutiny
            </button>
            <button className="btn-secondary" onClick={loadData} title="Refresh Data">
              <RefreshCw size={13} className={loading ? 'spin' : ''} />
            </button>
          </div>
        </div>
      </div>

      {/* Transactions Data Table */}
      <div className="data-table-wrapper" ref={tableRef}>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Product</th>
              <th>HS Code</th>
              <th>Trade Corridor</th>
              <th>Qty & Price</th>
              <th>Customs Value</th>
              <th>Duty Assessed</th>
              <th>GST / VAT</th>
              <th>Landed Cost</th>
              <th>Audit Verdict</th>
              <th>Inspect</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length > 0 ? (
              transactions.map((tx) => (
                <tr key={tx.Transaction_ID}>
                  <td className="mono" style={{ fontSize: 12, color: '#94a3b8' }}>#{tx.Transaction_ID}</td>
                  <td style={{ fontWeight: 500 }}>{tx.Product}</td>
                  <td className="mono" style={{ fontSize: 12, color: '#60a5fa' }}>{tx.HS_Code}</td>
                  <td>
                    <span style={{ color: '#94a3b8' }}>{tx.Origin_Country}</span>
                    {' '}&rarr;{' '}
                    <strong style={{ color: '#e2e8f0' }}>{tx.Destination_Country}</strong>
                  </td>
                  <td className="mono" style={{ fontSize: 12 }}>
                    {tx.Quantity} &times; ${tx.Unit_Price_USD}
                  </td>
                  <td className="mono">${tx.Customs_Value_USD?.toLocaleString()}</td>
                  <td className="mono" style={{ color: '#f59e0b' }}>
                    ${tx.Duty_USD?.toLocaleString()} ({tx.Duty_Rate_Percent}%)
                  </td>
                  <td className="mono">${tx.GST_VAT_USD?.toLocaleString()}</td>
                  <td className="mono" style={{ fontWeight: 600, color: '#fff' }}>
                    ${tx.Landing_Cost_USD?.toLocaleString()}
                  </td>
                  <td>
                    {tx.Audit_Status === 'FLAGGED' ? (
                      <span className="badge badge-warning">
                        <AlertCircle size={11} />
                        {tx.Audit_Reason}
                      </span>
                    ) : (
                      <span className="badge badge-success">
                        <CheckCircle2 size={11} />
                        Cleared
                      </span>
                    )}
                  </td>
                  <td>
                    <button
                      className="btn-secondary"
                      style={{ padding: '3px 8px', fontSize: 11 }}
                      onClick={() => setSelectedTx(tx)}
                    >
                      Audit
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={11} style={{ textAlign: 'center', padding: 32, color: '#64748b' }}>
                  {loading ? 'Executing batch audit queries...' : 'No transactions found matching your criteria.'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
        <div style={{ fontSize: 12, color: '#64748b' }}>
          Showing {page * limit + 1} - {Math.min((page + 1) * limit, total)} of {total} records
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className="btn-secondary"
            disabled={page === 0}
            onClick={() => setPage(p => Math.max(0, p - 1))}
          >
            Previous
          </button>
          <button
            className="btn-secondary"
            disabled={(page + 1) * limit >= total}
            onClick={() => setPage(p => p + 1)}
          >
            Next
          </button>
        </div>
      </div>

      {/* Detail Inspection Modal */}
      {selectedTx && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(5, 7, 10, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 24
        }}>
          <div className="card" style={{ maxWidth: 600, width: '100%' }}>
            <div className="card-header">
              <span className="card-title">
                Transaction Audit Inspector #{selectedTx.Transaction_ID}
              </span>
              <button className="btn-secondary" onClick={() => setSelectedTx(null)}>
                Close
              </button>
            </div>
            <div className="card-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>PRODUCT</div>
                  <div style={{ fontWeight: 600 }}>{selectedTx.Product}</div>
                  <div className="mono" style={{ fontSize: 12, color: '#60a5fa' }}>HS Code: {selectedTx.HS_Code}</div>
                </div>
                <div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>TRADE CORRIDOR</div>
                  <div>{selectedTx.Origin_Country} &rarr; {selectedTx.Destination_Country}</div>
                </div>
              </div>

              <table className="cost-table">
                <tbody>
                  <tr>
                    <td>Commercial Valuation ({selectedTx.Quantity} units @ ${selectedTx.Unit_Price_USD})</td>
                    <td className="mono">${selectedTx.Product_Cost_USD}</td>
                  </tr>
                  <tr>
                    <td>Shipping Freight Cost</td>
                    <td className="mono">${selectedTx.Shipping_USD}</td>
                  </tr>
                  <tr>
                    <td>Assessable Customs Value</td>
                    <td className="mono">${selectedTx.Customs_Value_USD}</td>
                  </tr>
                  <tr>
                    <td>Customs Import Duty ({selectedTx.Duty_Rate_Percent}%)</td>
                    <td className="mono" style={{ color: '#f59e0b' }}>+ ${selectedTx.Duty_USD}</td>
                  </tr>
                  <tr>
                    <td>GST / VAT</td>
                    <td className="mono" style={{ color: '#f59e0b' }}>+ ${selectedTx.GST_VAT_USD}</td>
                  </tr>
                  <tr className="total-row">
                    <td>Audited Landed Cost</td>
                    <td className="mono" style={{ color: '#34d399' }}>${selectedTx.Landing_Cost_USD}</td>
                  </tr>
                </tbody>
              </table>

              <div style={{ marginTop: 16, padding: 12, background: '#0e1017', borderRadius: 6, border: '1px solid #232938' }}>
                <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>AUDIT REASONING</div>
                <div style={{ fontSize: 12, color: '#e2e8f0' }}>
                  {selectedTx.Audit_Status === 'FLAGGED'
                    ? `Triggered compliance review: ${selectedTx.Audit_Reason}. Shipment exceeds standard clearance thresholds.`
                    : 'Standard customs documentation verified. No irregular tariff discrepancy detected.'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
