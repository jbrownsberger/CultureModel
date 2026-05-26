import React from 'react';
import { PRACTICE_COLORS, PRACTICE_LABELS } from './simulation';
import './ResultsDrawer.css';

export default function ResultsDrawer({ sim }) {
  const { model, currentStep } = sim;
  if (!model || currentStep === 0) {
    return <div className="results-empty"><p>Run the simulation to see results.</p></div>;
  }
  const { history, institutions } = model;
  const practiceTypes = [...new Set(Object.values(institutions).map(i => i.practiceType))];

  return (
    <div className="results-wrap">
      <div className="results-grid">
        <div className="result-card wide">
          <h3 className="result-card__title">Participation Rates Over Time</h3>
          <LineChart series={practiceTypes.map(p => ({
            key: p, label: PRACTICE_LABELS[p] || p,
            data: history[`${p}_rate`] || [], color: PRACTICE_COLORS[p] || '#999', asPercent: true,
          }))} height={220} yLabel="% participating" />
        </div>
        <div className="result-card wide">
          <h3 className="result-card__title">Average Hours per Week</h3>
          <LineChart series={practiceTypes.map(p => ({
            key: p, label: PRACTICE_LABELS[p] || p,
            data: history[`${p}_hours`] || [], color: PRACTICE_COLORS[p] || '#999', asPercent: false,
          }))} height={220} yLabel="hrs / week" stacked />
        </div>
        <div className="result-card">
          <h3 className="result-card__title">Institution Summary</h3>
          <table className="inst-table">
            <thead><tr><th>Institution</th><th>Type</th><th>Members</th><th>Fill</th><th>Avg hrs</th></tr></thead>
            <tbody>
              {Object.entries(institutions).map(([key, inst]) => {
                const members = [...inst.members];
                const avgHrs = members.length > 0
                  ? members.reduce((s, id) => s + (model.agents[id]?.timeAllocation[key] || 0), 0) / members.length : 0;
                const fill = inst.size > 0 ? (100 * inst.members.size / inst.size).toFixed(0) : 0;
                return (
                  <tr key={key}>
                    <td>{inst.name}</td>
                    <td><span className="type-pill" style={{ '--c': PRACTICE_COLORS[inst.practiceType] }}>{inst.practiceType.replace('_',' ')}</span></td>
                    <td>{inst.members.size}</td>
                    <td><div className="fill-bar"><div style={{ width: `${fill}%`, background: PRACTICE_COLORS[inst.practiceType] }} /></div>{fill}%</td>
                    <td>{avgHrs.toFixed(1)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="result-card">
          <h3 className="result-card__title">Final Distribution</h3>
          <FinalBar model={model} practiceTypes={practiceTypes} />
        </div>
      </div>
    </div>
  );
}

function LineChart({ series, height, yLabel }) {
  const W = 600; const H = height;
  const padL = 44; const padR = 16; const padT = 12; const padB = 28;
  const innerW = W - padL - padR; const innerH = H - padT - padB;
  if (!series.length || !series[0].data.length) return null;
  const steps = series[0].data.length;
  let yMax = 0;
  for (const s of series) yMax = Math.max(yMax, ...s.data);
  yMax = Math.ceil(yMax * 1.1 * 10) / 10 || 1;
  const xScale = i => padL + (i / Math.max(steps - 1, 1)) * innerW;
  const yScale = v => padT + innerH - (v / yMax) * innerH;
  const toPath = data => data.map((v, i) => `${i===0?'M':'L'} ${xScale(i).toFixed(1)} ${yScale(v).toFixed(1)}`).join(' ');
  const yTicks = [0, 0.25, 0.5, 0.75, 1.0].map(f => ({ val: yMax*f, y: yScale(yMax*f) }));
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} className="line-chart">
      {yTicks.map(t => <line key={t.val} x1={padL} y1={t.y} x2={W-padR} y2={t.y} stroke="#e5e7eb" strokeWidth={1} />)}
      {yTicks.map(t => (
        <text key={t.val} x={padL-6} y={t.y+4} textAnchor="end" fontSize={9} fill="#999">
          {series[0]?.asPercent ? `${(t.val*100).toFixed(0)}%` : t.val.toFixed(1)}
        </text>
      ))}
      {[0, Math.floor(steps/4), Math.floor(steps/2), Math.floor(3*steps/4), steps-1].filter(i => i < steps).map(i => (
        <text key={i} x={xScale(i)} y={H-8} textAnchor="middle" fontSize={9} fill="#999">{i}</text>
      ))}
      {series.map(s => <path key={s.key} d={toPath(s.data)} fill="none" stroke={s.color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" opacity={0.9} />)}
      <text x={10} y={H/2} textAnchor="middle" fontSize={9} fill="#999" transform={`rotate(-90, 10, ${H/2})`}>{yLabel}</text>
    </svg>
  );
}

function FinalBar({ model, practiceTypes }) {
  const { agents, institutions } = model;
  const counts = {};
  for (const agent of agents) {
    const totals = {};
    for (const [name, hours] of Object.entries(agent.timeAllocation)) {
      const inst = institutions[name];
      if (inst && inst.practiceType !== 'work') totals[inst.practiceType] = (totals[inst.practiceType] || 0) + hours;
    }
    const dom = Object.keys(totals).length ? Object.entries(totals).sort((a,b)=>b[1]-a[1])[0][0] : 'none';
    counts[dom] = (counts[dom] || 0) + 1;
  }
  const total = agents.length;
  return (
    <div className="final-bar-list">
      {Object.entries(counts).sort((a,b)=>b[1]-a[1]).map(([ptype, count]) => {
        const pct = (100 * count / total).toFixed(1);
        return (
          <div key={ptype} className="final-bar-row">
            <span className="final-bar-label">{PRACTICE_LABELS[ptype] || ptype}</span>
            <div className="final-bar-track">
              <div className="final-bar-fill" style={{ width: `${pct}%`, background: PRACTICE_COLORS[ptype] || '#999' }} />
            </div>
            <span className="final-bar-pct">{pct}%</span>
            <span className="final-bar-n">({count})</span>
          </div>
        );
      })}
    </div>
  );
}
