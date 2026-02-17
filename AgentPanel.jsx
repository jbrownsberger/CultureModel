import React from 'react';
import { getDominantPractice, getFreeTime, PRACTICE_COLORS, PRACTICE_LABELS, INSTITUTION_ICONS } from '../lib/simulation';
import './AgentPanel.css';

export default function AgentPanel({ agent, model, onClose }) {
  const { institutions, adjacency } = model;
  const dom     = getDominantPractice(agent, institutions);
  const color   = PRACTICE_COLORS[dom] || '#999';
  const nbrs    = [...(adjacency.get(agent.id) || [])];
  const freeTime = getFreeTime(agent);

  const alloc = Object.entries(agent.timeAllocation)
    .map(([name, hrs]) => ({ name, hrs, inst: institutions[name] }))
    .filter(x => x.hrs >= 0.5)
    .sort((a, b) => b.hrs - a.hrs);

  const totalAllocated = alloc.reduce((s, x) => s + x.hrs, 0);
  const totalHrs       = agent.timeBudget;

  const topValues = Object.entries(agent.values)
    .sort((a, b) => b[1] - a[1]);

  return (
    <div className="agent-panel">
      <div className="agent-panel__header" style={{ borderTopColor: color }}>
        <div className="agent-panel__title">
          <span className="agent-panel__dot" style={{ background: color }} />
          <span>Agent <strong>{agent.id}</strong></span>
          <span className="agent-panel__practice" style={{ color }}>
            {PRACTICE_LABELS[dom] || dom}
          </span>
        </div>
        <button className="agent-panel__close" onClick={onClose}>✕</button>
      </div>

      <div className="agent-panel__body">

        {/* Time allocation donut */}
        <section className="panel-section">
          <h3 className="panel-section__title">Time Allocation</h3>
          <DonutChart alloc={alloc} freeTime={freeTime} total={totalHrs} institutions={institutions} />
          <div className="alloc-list">
            {alloc.map(({ name, hrs, inst }) => {
              const pct = (100 * hrs / totalHrs).toFixed(0);
              const c   = PRACTICE_COLORS[inst?.practiceType] || '#999';
              return (
                <div key={name} className="alloc-row">
                  <span className="alloc-icon">{INSTITUTION_ICONS[inst?.practiceType] || '🏛'}</span>
                  <span className="alloc-name">{inst?.name || name}</span>
                  <div className="alloc-bar-wrap">
                    <div className="alloc-bar" style={{ width: `${pct}%`, background: c }} />
                  </div>
                  <span className="alloc-hrs">{hrs.toFixed(0)}h</span>
                </div>
              );
            })}
            {freeTime >= 0.5 && (
              <div className="alloc-row muted">
                <span className="alloc-icon">💤</span>
                <span className="alloc-name">Free time</span>
                <div className="alloc-bar-wrap">
                  <div className="alloc-bar" style={{ width: `${(100*freeTime/totalHrs).toFixed(0)}%`, background:'#ddd' }} />
                </div>
                <span className="alloc-hrs">{freeTime.toFixed(0)}h</span>
              </div>
            )}
          </div>
        </section>

        {/* Values radar */}
        <section className="panel-section">
          <h3 className="panel-section__title">Values</h3>
          <div className="values-grid">
            {topValues.map(([k, v]) => (
              <div key={k} className="value-bar-row">
                <span className="value-bar-label">{k}</span>
                <div className="value-bar-track">
                  <div className="value-bar-fill"
                    style={{ width: `${v * 100}%`, background: v > 0.7 ? color : '#999' }} />
                </div>
                <span className="value-bar-num">{v.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Network neighbours */}
        <section className="panel-section">
          <h3 className="panel-section__title">
            Connections <span className="count-badge">{nbrs.length}</span>
          </h3>
          <div className="nbr-grid">
            {nbrs.slice(0, 20).map(nbrId => {
              const nbr  = model.agents[nbrId];
              const ndom = getDominantPractice(nbr, institutions);
              return (
                <div key={nbrId} className="nbr-chip"
                  style={{ borderColor: PRACTICE_COLORS[ndom] || '#ccc' }}>
                  <span className="nbr-dot"
                    style={{ background: PRACTICE_COLORS[ndom] || '#999' }} />
                  {nbrId}
                </div>
              );
            })}
            {nbrs.length > 20 && (
              <span className="nbr-more">+{nbrs.length - 20} more</span>
            )}
          </div>
        </section>

        {/* Aware of */}
        <section className="panel-section">
          <h3 className="panel-section__title">
            Aware of <span className="count-badge">{agent.awareOf.size}</span>
          </h3>
          <div className="aware-list">
            {[...agent.awareOf].map(name => {
              const inst = institutions[name];
              const isMember = agent.institutions.has(name);
              return (
                <div key={name} className={`aware-item ${isMember ? 'member' : ''}`}>
                  <span>{INSTITUTION_ICONS[inst?.practiceType] || '🏛'}</span>
                  <span>{inst?.name || name}</span>
                  {isMember && <span className="member-badge">member</span>}
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}

function DonutChart({ alloc, freeTime, total, institutions }) {
  const size   = 100;
  const cx     = size / 2;
  const cy     = size / 2;
  const r      = 36;
  const stroke = 14;

  const segments = [
    ...alloc.map(({ name, hrs, inst }) => ({
      hrs,
      color: PRACTICE_COLORS[inst?.practiceType] || '#999',
    })),
    ...(freeTime >= 0.5 ? [{ hrs: freeTime, color: '#e5e7eb' }] : []),
  ];

  let cumAngle = -90; // start at top
  const paths = segments.map(({ hrs, color }) => {
    const pct       = hrs / total;
    const angle     = pct * 360;
    const startRad  = (cumAngle * Math.PI) / 180;
    const endRad    = ((cumAngle + angle) * Math.PI) / 180;
    const x1 = cx + r * Math.cos(startRad);
    const y1 = cy + r * Math.sin(startRad);
    const x2 = cx + r * Math.cos(endRad);
    const y2 = cy + r * Math.sin(endRad);
    const large = angle > 180 ? 1 : 0;
    const d  = `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
    cumAngle += angle;
    return { d, color, strokeWidth: stroke };
  });

  return (
    <svg width={size} height={size} className="donut-chart">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#eee" strokeWidth={stroke} />
      {paths.map((p, i) => (
        <path key={i} d={p.d} fill="none" stroke={p.color}
          strokeWidth={p.strokeWidth} strokeLinecap="butt" />
      ))}
      <text x={cx} y={cy+4} textAnchor="middle"
        fontSize={11} fontFamily="var(--font-mono)" fill="var(--ink-soft)">
        168h
      </text>
    </svg>
  );
}
