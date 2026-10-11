import React, { useState, useEffect, useRef } from 'react';
import { Search, BookOpen, ShieldCheck, Globe, Tag, ExternalLink } from 'lucide-react';
import gsap from 'gsap';
import { fetchPolicies } from '../api';

const CATEGORIES = [
  'All Categories',
  'Electronics',
  'Machinery',
  'Textiles',
  'Chemicals',
  'Food & Agriculture',
  'Automotive',
  'Pharmaceuticals'
];

export default function PolicyExplorer({ countries = [] }) {
  const [policies, setPolicies] = useState([]);
  const [query, setQuery] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All Categories');
  const [loading, setLoading] = useState(false);

  const gridRef = useRef(null);

  const loadPolicies = async () => {
    setLoading(true);
    try {
      const cat = selectedCategory === 'All Categories' ? '' : selectedCategory;
      const data = await fetchPolicies({
        query,
        country: selectedCountry,
        category: cat,
        limit: 60
      });
      setPolicies(data.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPolicies();
  }, [selectedCountry, selectedCategory]);

  // GSAP animation on policies update
  useEffect(() => {
    if (gridRef.current) {
      const cards = gridRef.current.querySelectorAll('.card');
      gsap.fromTo(
        cards,
        { opacity: 0, y: 15 },
        { opacity: 1, y: 0, duration: 0.4, stagger: 0.03, ease: 'power2.out' }
      );
    }
  }, [policies]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadPolicies();
  };

  return (
    <div>
      {/* Search & Filter Header */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-body">
          <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', flex: 1, minWidth: 280 }}>
              <Search size={14} style={{ position: 'absolute', left: 12, top: 12, color: '#64748b' }} />
              <input
                type="text"
                className="form-input"
                style={{ paddingLeft: 34 }}
                placeholder="Semantic query (e.g. India electronics BIS certification, medical device CE mark)..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>

            <select
              className="form-select"
              style={{ width: 180 }}
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
            >
              <option value="">All Countries</option>
              {countries.map(c => (
                <option key={c.Country} value={c.Country}>{c.Country}</option>
              ))}
            </select>

            <button type="submit" className="btn-primary" style={{ width: 'auto', padding: '0 20px' }}>
              Search Policies
            </button>
          </form>

          {/* Category Chips */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 14 }}>
            {CATEGORIES.map(cat => (
              <button
                key={cat}
                type="button"
                className={`preset-chip ${selectedCategory === cat ? 'active' : ''}`}
                style={selectedCategory === cat ? { backgroundColor: '#1e2433', color: '#fff', borderColor: '#3b82f6' } : {}}
                onClick={() => setSelectedCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Policies Grid with GSAP ref */}
      <div 
        ref={gridRef}
        style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 16 }}
      >
        {policies.length > 0 ? (
          policies.map((p) => (
            <div 
              key={p.Policy_ID || Math.random()} 
              className="card"
              onMouseEnter={(e) => gsap.to(e.currentTarget, { y: -3, duration: 0.2, ease: 'power1.out' })}
              onMouseLeave={(e) => gsap.to(e.currentTarget, { y: 0, duration: 0.2, ease: 'power1.out' })}
            >
              <div className="card-header" style={{ padding: '12px 16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Globe size={14} style={{ color: '#60a5fa' }} />
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{p.Country}</span>
                  <span className="mono" style={{ fontSize: 11, color: '#94a3b8' }}>
                    #{p.Policy_ID}
                  </span>
                </div>
                <span className="brand-badge">{p.Category}</span>
              </div>

              <div className="card-body" style={{ padding: '14px 16px' }}>
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 11, textTransform: 'uppercase', color: '#64748b', marginBottom: 2 }}>
                    Policy Provision
                  </div>
                  <div style={{ fontSize: 13, color: '#f3f4f6', lineHeight: 1.5 }}>
                    {p.Policy_Summary}
                  </div>
                </div>

                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 11, textTransform: 'uppercase', color: '#64748b', marginBottom: 2 }}>
                    Compliance & Regulatory Directives
                  </div>
                  <div style={{ fontSize: 12, color: '#9ca3af', background: '#0c0e14', padding: '8px 10px', borderRadius: 4, border: '1px solid #232938' }}>
                    {p.Compliance_Note}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 11, color: '#64748b' }}>
                  <span>Source: {p.Source_Type || 'National Customs Authority'}</span>
                  {p.relevance_score && (
                    <span className="mono" style={{ color: '#10b981' }}>Score: {p.relevance_score}</span>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="card" style={{ gridColumn: '1 / -1', padding: 48, textAlign: 'center', color: '#64748b' }}>
            {loading ? 'Retrieving trade policies from vector database...' : 'No trade policies matched your query.'}
          </div>
        )}
      </div>
    </div>
  );
}
