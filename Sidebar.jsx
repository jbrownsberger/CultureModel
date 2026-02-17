import React, { useState } from 'react';
import { INSTITUTION_ICONS, PRACTICE_COLORS } from '../lib/simulation';
import './Sidebar.css';

const PRESETS = {
  'Traditional': {
    community: [0.75, 0.15], tradition: [0.80, 0.12],
    growth:    [0.40, 0.20], civic:     [0.60, 0.18],
    status:    [0.30, 0.18], leisure:   [0.50, 0.20], wealth: [0.35, 0.18],
  },
  'Secular Urban': {
    community: [0.40, 0.20], tradition: [0.20, 0.15],
    growth:    [0.70, 0.18], civic:     [0.40, 0.20],
    status:    [0.70, 0.18], leisure:   [0.60, 0.20], wealth: [0.70, 0.18],
  },
  'Status-Driven': {
    community: [0.30, 0.18], tradition: [0.35, 0.18],
    growth:    [0.60, 0.18], civic:     [0.25, 0.18],
    status:    [0.90, 0.08], leisure:   [0.25, 0.18], wealth: [0.80, 0.12],
  },
};

const QUICK_INSTS = [
  { label: '🏢 Workplace',  type: 'work',          size: 40, money_cost:0,  money_income:25, culture:{community:0.3,tradition:0.2,growth:0.4,civic:0.2,status:0.5} },
  { label: '⛪ Church',     type: 'church',         size: 30, money_cost:2,  money_income:0,  culture:{community:0.8,tradition:0.9,growth:0.3,civic:0.5,status:0.3} },
  { label: '🎳 Club',       type: 'club',           size: 25, money_cost:5,  money_income:0,  culture:{community:0.6,tradition:0.2,growth:0.5,civic:0.3,status:0.5} },
  { label: '🏫 School',     type: 'education',      size: 35, money_cost:10, money_income:0,  culture:{community:0.4,tradition:0.4,growth:0.9,civic:0.5,status:0.7} },
  { label: '🏛 Civic org',  type: 'political_org',  size: 20, money_cost:0,  money_income:0,  culture:{community:0.5,tradition:0.3,growth:0.4,civic:0.9,status:0.4} },
];

export default function Sidebar({ sim, activeTab }) {
  const [section, setSection] = useState('institutions'); // 'institutions'|'population'|'params'
  const [customForm, setCustomForm] = useState({
    name: '', type: 'club', size: 25, money_cost: 0, money_income: 0,
    culture: { community: 0, tradition: 0, growth: 0, civic: 0, status: 0 },
  });
  const [showCustom, setShowCustom] = useState(false);

  const addQuick = (template) => {
    const n = sim.institutions.filter(i => i.type === template.type).length + 1;
    sim.addInstitution({
      ...template,
      name: `${template.type.replace('_',' ')} ${n}`,
    });
  };

  const addCustom = () => {
    if (!customForm.name.trim()) return;
    sim.addInstitution({ ...customForm });
    setCustomForm({
      name: '', type: 'club', size: 25, money_cost: 0, money_income: 0,
      culture: { community: 0, tradition: 0, growth: 0, civic: 0, status: 0 },
    });
    setShowCustom(false);
  };

  return (
    <aside className="sidebar">
      {/* Section switcher */}
      <div className="sidebar-tabs">
        {[['institutions','Institutions'],['population','Population'],['params','Params']].map(([k,l]) => (
          <button key={k} className={`sidebar-tab ${section===k?'active':''}`}
            onClick={() => setSection(k)}>{l}</button>
        ))}
      </div>

      <div className="sidebar-content">

        {/* ── INSTITUTIONS ─────────────────────────────────────────── */}
        {section === 'institutions' && (
          <>
            <p className="sidebar-hint">
              Quick-add common types, or define a custom institution below.
            </p>

            <div className="quick-grid">
              {QUICK_INSTS.map(qi => (
                <button key={qi.type} className="quick-btn"
                  style={{ '--accent-c': PRACTICE_COLORS[qi.type] }}
                  onClick={() => addQuick(qi)}>
                  <span className="quick-icon">{qi.label.split(' ')[0]}</span>
                  <span className="quick-label">{qi.label.split(' ').slice(1).join(' ')}</span>
                </button>
              ))}
            </div>

            <button className="toggle-custom-btn"
              onClick={() => setShowCustom(v => !v)}>
              {showCustom ? '▲ Hide custom' : '▼ Custom institution…'}
            </button>

            {showCustom && (
              <div className="custom-form">
                <label className="field-label">Name
                  <input className="field-input" value={customForm.name}
                    onChange={e => setCustomForm(f => ({...f, name: e.target.value}))}
                    placeholder="e.g. First Baptist" />
                </label>

                <label className="field-label">Type
                  <select className="field-select" value={customForm.type}
                    onChange={e => setCustomForm(f => ({...f, type: e.target.value}))}>
                    {Object.keys(INSTITUTION_ICONS).map(t => (
                      <option key={t} value={t}>{INSTITUTION_ICONS[t]} {t.replace('_',' ')}</option>
                    ))}
                  </select>
                </label>

                <div className="field-row">
                  <label className="field-label half">Max members
                    <input className="field-input" type="number" min="5" max="100"
                      value={customForm.size}
                      onChange={e => setCustomForm(f => ({...f, size: +e.target.value}))} />
                  </label>
                  <label className="field-label half">Cost $/hr
                    <input className="field-input" type="number" min="0" step="0.5"
                      value={customForm.money_cost}
                      onChange={e => setCustomForm(f => ({...f, money_cost: +e.target.value}))} />
                  </label>
                </div>

                <label className="field-label">Income $/hr
                  <input className="field-input" type="number" min="0" step="1"
                    value={customForm.money_income}
                    onChange={e => setCustomForm(f => ({...f, money_income: +e.target.value}))} />
                </label>

                <p className="field-label" style={{marginBottom:4}}>Culture values</p>
                {Object.keys(customForm.culture).map(v => (
                  <label key={v} className="mini-slider">
                    <span>{v}</span>
                    <input type="range" min="-1" max="1" step="0.1"
                      value={customForm.culture[v]}
                      onChange={e => setCustomForm(f => ({...f,
                        culture:{...f.culture,[v]:+e.target.value}}))} />
                    <span className="mini-val">{customForm.culture[v].toFixed(1)}</span>
                  </label>
                ))}

                <button className="add-btn" onClick={addCustom}
                  disabled={!customForm.name.trim()}>
                  ➕ Add
                </button>
              </div>
            )}

            {/* Institution list */}
            <div className="inst-list">
              {sim.institutions.length === 0 && (
                <p className="sidebar-hint muted">No institutions yet.</p>
              )}
              {sim.institutions.map((inst, idx) => (
                <div key={idx} className="inst-item"
                  style={{ '--inst-color': PRACTICE_COLORS[inst.type] || '#999' }}>
                  <span className="inst-icon">{INSTITUTION_ICONS[inst.type] || '🏛'}</span>
                  <div className="inst-info">
                    <span className="inst-name">{inst.name}</span>
                    <span className="inst-meta">
                      {inst.size} cap · ${inst.money_cost}/h
                      {inst.money_income > 0 && ` · $${inst.money_income}/h`}
                    </span>
                  </div>
                  <button className="inst-remove" onClick={() => sim.removeInstitution(idx)}>×</button>
                </div>
              ))}
            </div>
          </>
        )}

        {/* ── POPULATION ───────────────────────────────────────────── */}
        {section === 'population' && (
          <>
            <p className="sidebar-hint">Set mean and spread for each value.</p>

            <div className="preset-row">
              {Object.keys(PRESETS).map(name => (
                <button key={name} className="preset-btn"
                  onClick={() => sim.applyPreset(
                    Object.fromEntries(Object.entries(PRESETS[name]).map(([k,v]) => [k,v]))
                  )}>
                  {name}
                </button>
              ))}
            </div>

            {Object.entries(sim.valueSettings).map(([vname, [mean, std]]) => (
              <div key={vname} className="value-row">
                <span className="value-name">{vname}</span>
                <div className="value-sliders">
                  <label className="mini-slider">
                    <span className="mini-label">μ</span>
                    <input type="range" min="0" max="1" step="0.05" value={mean}
                      onChange={e => sim.setValueSettings(prev => ({
                        ...prev, [vname]: [+e.target.value, std]
                      }))} />
                    <span className="mini-val">{mean.toFixed(2)}</span>
                  </label>
                  <label className="mini-slider">
                    <span className="mini-label">σ</span>
                    <input type="range" min="0" max="0.4" step="0.02" value={std}
                      onChange={e => sim.setValueSettings(prev => ({
                        ...prev, [vname]: [mean, +e.target.value]
                      }))} />
                    <span className="mini-val">{std.toFixed(2)}</span>
                  </label>
                </div>
              </div>
            ))}
          </>
        )}

        {/* ── PARAMS ───────────────────────────────────────────────── */}
        {section === 'params' && (
          <>
            {[
              ['nAgents',         'Agents',             30,  200,  10,   'integer'],
              ['networkDensity',   'Background density', 0.01,0.10, 0.005,'float'],
              ['awarenessRadius',  'Awareness radius',   0.1, 0.6,  0.02, 'float'],
              ['reallocFreq',      'Reoptimise every N steps', 1, 10, 1, 'integer'],
              ['seed',             'Random seed',        0,   9999, 1,   'integer'],
            ].map(([key, label, min, max, step, type]) => (
              <label key={key} className="field-label">
                {label}
                <div className="param-row">
                  <input type="range" min={min} max={max} step={step}
                    value={sim.params[key]}
                    onChange={e => sim.setParams(p => ({
                      ...p, [key]: type==='integer' ? +e.target.value : +e.target.value
                    }))} />
                  <span className="param-val">
                    {type === 'float' ? sim.params[key].toFixed(3) : sim.params[key]}
                  </span>
                </div>
              </label>
            ))}
          </>
        )}
      </div>
    </aside>
  );
}
