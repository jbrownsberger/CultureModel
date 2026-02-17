import React, { useRef, useState, useEffect, useCallback } from 'react';
import { getDominantPractice, PRACTICE_COLORS, INSTITUTION_ICONS, getFreeTime } from '../lib/simulation';
import './MapView.css';

const INST_SHAPES = {
  work:             'M -9,-9 L 9,-9 L 9,9 L -9,9 Z',           // square
  church:           'M 0,-11 L 9,4 L -9,4 Z',                   // triangle
  club:             'M 0,-10 L 3,-3 L 10,-3 L 5,2 L 7,10 L 0,5 L -7,10 L -5,2 L -10,-3 L -3,-3 Z', // star
  education:        'M 0,-10 L 10,5 L -10,5 Z',                  // triangle-up
  political_org:    'M 0,-10 L 9,-4 L 9,5 L -9,5 L -9,-4 Z',   // pentagon-ish
  community_center: 'M -8,-5 L 0,-11 L 8,-5 L 8,8 L -8,8 Z',   // house
};

export default function MapView({ sim, selectedAgent, onAgentClick, onMapClick }) {
  const svgRef      = useRef(null);
  const [dims, setDims] = useState({ w: 800, h: 600 });
  const [tooltip, setTooltip] = useState(null);
  const [hoverInst, setHoverInst] = useState(null);

  // Observe container size
  useEffect(() => {
    if (!svgRef.current) return;
    const ro = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect;
      setDims({ w: width, h: height });
    });
    ro.observe(svgRef.current.parentElement);
    return () => ro.disconnect();
  }, []);

  // Convert [0,1] model coords to SVG pixels
  const px = useCallback((x) => 40 + x * (dims.w - 80), [dims.w]);
  const py = useCallback((y) => 40 + y * (dims.h - 80), [dims.h]);

  const { model } = sim;

  if (!model) {
    return (
      <div className="map-empty">
        <div className="map-empty__inner">
          <span className="map-empty__icon">⬡</span>
          <p className="map-empty__title">No model yet</p>
          <p className="map-empty__sub">Add institutions in the sidebar, then click Initialise.</p>
        </div>
      </div>
    );
  }

  const { agents, institutions, adjacency } = model;

  // Build edge list (sample for performance if large)
  const edges = [];
  const maxEdges = 600;
  let edgeCount = 0;
  for (const [aId, nbrs] of adjacency) {
    for (const bId of nbrs) {
      if (bId > aId) {
        if (edgeCount < maxEdges) {
          edges.push([aId, bId]);
          edgeCount++;
        }
      }
    }
  }

  const selectedNeighbors = selectedAgent
    ? new Set(adjacency.get(selectedAgent.id) || [])
    : new Set();

  return (
    <div className="map-wrap">
      {/* Awareness radius legend */}
      <div className="map-legend">
        {Object.entries(PRACTICE_COLORS).filter(([k]) => k !== 'none').map(([k, c]) => (
          <span key={k} className="legend-item">
            <span className="legend-dot" style={{ background: c }} />
            {k.replace('_', ' ')}
          </span>
        ))}
      </div>

      <svg
        ref={svgRef}
        className="map-svg"
        width={dims.w}
        height={dims.h}
        onClick={onMapClick}
      >
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
            <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
          {/* Awareness circle pattern */}
          <radialGradient id="awareness-grad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="currentColor" stopOpacity="0.06"/>
            <stop offset="100%" stopColor="currentColor" stopOpacity="0"/>
          </radialGradient>
        </defs>

        {/* Institution awareness halos */}
        {Object.entries(institutions).map(([name, inst]) => {
          const r = sim.params.awarenessRadius * (dims.w - 80);
          const color = PRACTICE_COLORS[inst.practiceType] || '#999';
          return (
            <circle
              key={`halo-${name}`}
              cx={px(inst.position[0])}
              cy={py(inst.position[1])}
              r={r}
              fill={color}
              fillOpacity={hoverInst === name ? 0.10 : 0.04}
              stroke={color}
              strokeOpacity={0.15}
              strokeWidth={1}
              strokeDasharray="4 4"
              style={{ pointerEvents: 'none', transition: 'fill-opacity 0.2s' }}
            />
          );
        })}

        {/* Edges */}
        <g className="edges" opacity={selectedAgent ? 0.12 : 0.18}>
          {edges.map(([a, b]) => (
            <line
              key={`e-${a}-${b}`}
              x1={px(agents[a].position[0])} y1={py(agents[a].position[1])}
              x2={px(agents[b].position[0])} y2={py(agents[b].position[1])}
              stroke="#0f1117"
              strokeWidth={0.8}
            />
          ))}
        </g>

        {/* Selected agent's edges highlighted */}
        {selectedAgent && [...selectedNeighbors].map(nbrId => (
          <line
            key={`sel-e-${nbrId}`}
            x1={px(selectedAgent.position[0])} y1={py(selectedAgent.position[1])}
            x2={px(agents[nbrId].position[0])} y2={py(agents[nbrId].position[1])}
            stroke={PRACTICE_COLORS[getDominantPractice(selectedAgent, institutions)] || '#666'}
            strokeWidth={1.5}
            opacity={0.55}
          />
        ))}

        {/* Agents */}
        {agents.map(agent => {
          const dom     = getDominantPractice(agent, institutions);
          const color   = PRACTICE_COLORS[dom] || PRACTICE_COLORS.none;
          const isSel   = selectedAgent?.id === agent.id;
          const isNbr   = selectedNeighbors.has(agent.id);
          const dimmed  = selectedAgent && !isSel && !isNbr;
          const r       = isSel ? 8 : isNbr ? 6.5 : 5.5;

          return (
            <g
              key={agent.id}
              transform={`translate(${px(agent.position[0])},${py(agent.position[1])})`}
              onClick={e => { e.stopPropagation(); onAgentClick(agent); }}
              onMouseEnter={() => setTooltip({ type: 'agent', agent })}
              onMouseLeave={() => setTooltip(null)}
              style={{ cursor: 'pointer' }}
            >
              {isSel && (
                <circle r={r + 4} fill="none" stroke={color} strokeWidth={2} opacity={0.5}
                  filter="url(#glow)" />
              )}
              <circle
                r={r}
                fill={color}
                fillOpacity={dimmed ? 0.18 : 1}
                stroke={isSel ? 'white' : 'rgba(255,255,255,0.6)'}
                strokeWidth={isSel ? 2 : 1}
                style={{ transition: 'r 0.15s, fill-opacity 0.15s' }}
              />
            </g>
          );
        })}

        {/* Institution markers */}
        {Object.entries(institutions).map(([name, inst]) => {
          const color = PRACTICE_COLORS[inst.practiceType] || '#555';
          const shape = INST_SHAPES[inst.practiceType] || INST_SHAPES.work;
          const x     = px(inst.position[0]);
          const y     = py(inst.position[1]);
          const isHov = hoverInst === name;

          return (
            <g
              key={name}
              transform={`translate(${x},${y})`}
              onMouseEnter={() => { setHoverInst(name); setTooltip({ type: 'inst', name, inst }); }}
              onMouseLeave={() => { setHoverInst(null); setTooltip(null); }}
              onClick={e => e.stopPropagation()}
              style={{ cursor: 'default' }}
            >
              {/* Shadow */}
              <path d={shape} fill="rgba(0,0,0,0.15)" transform="translate(2,3) scale(1.3)" />
              {/* Body */}
              <path
                d={shape}
                fill={color}
                stroke="white"
                strokeWidth={isHov ? 2.5 : 1.5}
                transform="scale(1.3)"
                filter={isHov ? 'url(#glow)' : undefined}
                style={{ transition: 'transform 0.15s' }}
              />
              {/* Member count badge */}
              <circle cx={10} cy={-10} r={8} fill="white" stroke={color} strokeWidth={1.5} />
              <text x={10} y={-6} textAnchor="middle"
                fontSize={8} fontFamily="var(--font-mono)" fill={color} fontWeight="600">
                {inst.members.size}
              </text>
              {/* Name label */}
              <text y={20} textAnchor="middle"
                fontSize={9} fontFamily="var(--font-body)" fill="var(--ink)"
                stroke="var(--paper)" strokeWidth={3} paintOrder="stroke">
                {inst.name}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Tooltip */}
      {tooltip && <Tooltip tooltip={tooltip} institutions={institutions} />}
    </div>
  );
}

function Tooltip({ tooltip, institutions }) {
  if (tooltip.type === 'agent') {
    const { agent } = tooltip;
    const dom = getDominantPractice(agent, institutions);
    const alloc = Object.entries(agent.timeAllocation)
      .sort((a, b) => b[1] - a[1]).slice(0, 4);

    return (
      <div className="map-tooltip">
        <div className="tooltip-header">
          <span className="tooltip-dot"
            style={{ background: PRACTICE_COLORS[dom] || '#999' }} />
          Agent {agent.id}
        </div>
        <div className="tooltip-body">
          {alloc.map(([name, hrs]) => (
            <div key={name} className="tooltip-row">
              <span>{institutions[name]?.name || name}</span>
              <span className="tooltip-val">{hrs.toFixed(0)} h</span>
            </div>
          ))}
          <div className="tooltip-row muted">
            <span>Free time</span>
            <span className="tooltip-val">{getFreeTime(agent).toFixed(0)} h</span>
          </div>
        </div>
      </div>
    );
  }

  if (tooltip.type === 'inst') {
    const { name, inst } = tooltip;
    return (
      <div className="map-tooltip">
        <div className="tooltip-header">
          <span>{INSTITUTION_ICONS[inst.practiceType] || '🏛'}</span>
          {inst.name}
        </div>
        <div className="tooltip-body">
          <div className="tooltip-row">
            <span>Members</span>
            <span className="tooltip-val">{inst.members.size} / {inst.size}</span>
          </div>
          <div className="tooltip-row">
            <span>Type</span>
            <span className="tooltip-val">{inst.practiceType.replace('_',' ')}</span>
          </div>
          {inst.moneyCostPerHour > 0 && (
            <div className="tooltip-row">
              <span>Cost</span>
              <span className="tooltip-val">${inst.moneyCostPerHour}/h</span>
            </div>
          )}
          {inst.moneyIncomePerHour > 0 && (
            <div className="tooltip-row">
              <span>Income</span>
              <span className="tooltip-val">${inst.moneyIncomePerHour}/h</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
}
