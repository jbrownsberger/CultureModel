// Core simulation model — ported from Python

export const PRACTICE_COLORS = {
  work:             '#c1440e',
  church:           '#7c3aed',
  club:             '#1d6fa4',
  education:        '#1a6b4a',
  political_org:    '#b45309',
  community_center: '#0e7490',
  none:             '#9ca3af',
};

export const PRACTICE_LABELS = {
  work:             'Work',
  church:           'Church',
  club:             'Club',
  education:        'Education',
  political_org:    'Civic Org',
  community_center: 'Comm. Center',
  none:             'None',
};

export const INSTITUTION_ICONS = {
  work:             '🏢',
  church:           '⛪',
  club:             '🎳',
  education:        '🏫',
  political_org:    '🏛',
  community_center: '🏡',
};

const PRACTICE_PROFILES = {
  work:             { optimalHours: 40, dr: 1.5, benefits: { community:0.01, tradition:0.0, growth:0.02, civic:0.01, status:0.03, leisure:-0.05, wealth:0.0 } },
  church:           { optimalHours: 10, dr: 1.3, benefits: { community:0.15, tradition:0.12, growth:0.05, civic:0.06, status:0.04, leisure:0.0, wealth:0.0 } },
  club:             { optimalHours:  6, dr: 1.4, benefits: { community:0.10, tradition:0.02, growth:0.08, civic:0.03, status:0.06, leisure:0.05, wealth:0.0 } },
  education:        { optimalHours: 20, dr: 1.1, benefits: { community:0.05, tradition:0.04, growth:0.15, civic:0.05, status:0.10, leisure:0.0, wealth:0.0 } },
  political_org:    { optimalHours: 15, dr: 1.2, benefits: { community:0.07, tradition:0.03, growth:0.06, civic:0.15, status:0.09, leisure:0.0, wealth:0.0 } },
  community_center: { optimalHours: 30, dr: 1.2, benefits: { community:0.12, tradition:0.08, growth:0.04, civic:0.02, status:0.02, leisure:0.08, wealth:0.0 } },
};

const MAX_HOURS = { work:60, church:20, club:15, political_org:30, education:40, community_center:50 };

// ── Seeded RNG for reproducibility ──────────────────────────────────────────
function mulberry32(seed) {
  return function() {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

// ── Agent ────────────────────────────────────────────────────────────────────
function createAgent(id, rand) {
  return {
    id,
    position: [rand(), rand()],
    values: {
      community: rand(),
      tradition: rand(),
      growth:    rand(),
      civic:     rand(),
      status:    rand(),
      leisure:   rand(),
      wealth:    rand(),
    },
    timeBudget:  168,
    moneyBudget: 500 + rand() * 1500,
    timeAllocation: {},     // { instName: hours }
    institutions: new Set(),
    awareOf:      new Set(),
    commStrength: 0.5 + rand() * 0.5,
    stepsSinceChange: 100,
  };
}

function applyValueSettings(agent, valueSettings, rand) {
  for (const [k, [mean, std]] of Object.entries(valueSettings)) {
    // Box-Muller for normal distribution
    const u1 = Math.max(1e-10, rand());
    const u2 = rand();
    const z  = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    agent.values[k] = Math.min(1, Math.max(0, mean + z * std));
  }
}

function getFreeTime(agent) {
  return agent.timeBudget - Object.values(agent.timeAllocation).reduce((s, h) => s + h, 0);
}

function getDominantPractice(agent, institutions) {
  const totals = {};
  for (const [name, hours] of Object.entries(agent.timeAllocation)) {
    const inst = institutions[name];
    if (inst && inst.practiceType !== 'work') {
      totals[inst.practiceType] = (totals[inst.practiceType] || 0) + hours;
    }
  }
  if (!Object.keys(totals).length) return 'none';
  return Object.entries(totals).sort((a, b) => b[1] - a[1])[0][0];
}

// ── Institution ──────────────────────────────────────────────────────────────
function createInstitution(config, rand) {
  return {
    name:              config.name,
    practiceType:      config.type,
    size:              config.size,
    members:           new Set(),
    culture:           { ...config.culture },
    moneyCostPerHour:  config.money_cost || 0,
    moneyIncomePerHour:config.money_income || 0,
    position:          [rand(), rand()],
  };
}

// ── Utility calculations ─────────────────────────────────────────────────────
function calcUtility(agent, instName, hours, institutions) {
  if (hours <= 0) return 0;
  const inst    = institutions[instName];
  if (!inst) return 0;
  const profile = PRACTICE_PROFILES[inst.practiceType];
  if (!profile) return 0;

  const eff = Math.pow(hours, 1 / profile.dr);
  let u = 0;
  for (const [dim, benefit] of Object.entries(profile.benefits)) {
    u += benefit * (agent.values[dim] || 0) * eff;
  }
  if (inst.practiceType === 'work') {
    u += hours * inst.moneyIncomePerHour * (agent.values.wealth || 0) * 0.01;
  } else {
    u -= hours * inst.moneyCostPerHour  * (agent.values.wealth || 0) * 0.01;
  }
  return u;
}

function marginalUtility(agent, instName, currentHours, institutions) {
  return calcUtility(agent, instName, currentHours + 1, institutions)
       - calcUtility(agent, instName, currentHours,     institutions);
}

function optimizeAllocation(agent, institutions) {
  const allocation = {};
  for (const name of agent.awareOf) allocation[name] = 0;
  let timeLeft = agent.timeBudget;

  for (let iter = 0; iter < agent.timeBudget; iter++) {
    if (timeLeft <= 0) break;

    let bestInst = null, bestMU = 0.005;

    for (const name of agent.awareOf) {
      const inst = institutions[name];
      if (!inst) continue;
      const cur    = allocation[name] || 0;
      const maxHrs = MAX_HOURS[inst.practiceType] || 50;
      if (cur >= maxHrs) continue;

      // Affordability
      if (inst.practiceType !== 'work') {
        const income = Object.entries(allocation)
          .reduce((s, [n, h]) => s + h * (institutions[n]?.moneyIncomePerHour || 0), 0);
        const costs  = Object.entries(allocation)
          .reduce((s, [n, h]) => s + h * (institutions[n]?.moneyCostPerHour  || 0), 0);
        const bal    = agent.moneyBudget + income - costs;
        if (bal - inst.moneyCostPerHour < 0) continue;
      }

      const mu = marginalUtility(agent, name, cur, institutions);
      if (mu > bestMU) { bestMU = mu; bestInst = name; }
    }

    if (!bestInst) break;
    allocation[bestInst] = (allocation[bestInst] || 0) + 1;
    timeLeft--;
  }

  return Object.fromEntries(Object.entries(allocation).filter(([, h]) => h >= 0.5));
}

// ── Network ──────────────────────────────────────────────────────────────────
function buildAdjacency(n, density, rand) {
  // Sparse adjacency as Map<id, Set<id>>
  const adj = new Map();
  for (let i = 0; i < n; i++) adj.set(i, new Set());

  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if (rand() < density) {
        adj.get(i).add(j);
        adj.get(j).add(i);
      }
    }
  }
  return adj;
}

function addInstitutionalEdges(adjacency, institutions, agents) {
  for (const inst of Object.values(institutions)) {
    const members = [...inst.members];
    for (let i = 0; i < members.length; i++) {
      for (let j = i + 1; j < members.length; j++) {
        const a = members[i], b = members[j];
        adjacency.get(a).add(b);
        adjacency.get(b).add(a);
      }
    }
  }
}

// ── Broadcast awareness ──────────────────────────────────────────────────────
function broadcastAwareness(agents, institutions, radius) {
  for (const agent of agents) {
    for (const [name, inst] of Object.entries(institutions)) {
      const dx = agent.position[0] - inst.position[0];
      const dy = agent.position[1] - inst.position[1];
      if (Math.sqrt(dx*dx + dy*dy) <= radius) {
        agent.awareOf.add(name);
      }
    }
  }
}

// ── Main model factory ───────────────────────────────────────────────────────
export function createModel(config) {
  const {
    nAgents         = 100,
    institutionDefs = [],
    valueSettings   = {},
    networkDensity  = 0.03,
    awarenessRadius = 0.3,
    reallocFreq     = 4,
    seed            = 42,
  } = config;

  const rand = mulberry32(seed);

  // Create agents
  const agents = Array.from({ length: nAgents }, (_, i) => {
    const a = createAgent(i, rand);
    applyValueSettings(a, valueSettings, rand);
    return a;
  });

  // Create institutions
  const institutions = {};
  for (const def of institutionDefs) {
    const key = `${def.type}_${def.name.replace(/\s+/g,'_')}`;
    institutions[key] = createInstitution(def, rand);
  }

  // Broadcast spatial awareness
  broadcastAwareness(agents, institutions, awarenessRadius);

  // Initial memberships
  for (const agent of agents) {
    for (const instName of agent.awareOf) {
      const inst = institutions[instName];
      if (!inst) continue;
      const fit = Object.entries(inst.culture)
        .reduce((s, [k, v]) => s + v * (agent.values[k] || 0), 0);
      if (fit > 0 && rand() < 0.3 && inst.members.size < inst.size) {
        inst.members.add(agent.id);
        agent.institutions.add(instName);
        const hrs = inst.practiceType === 'work'   ? 40
                  : inst.practiceType === 'church'  ? 3 + rand() * 5
                  : inst.practiceType === 'club'    ? 2 + rand() * 4
                  : inst.practiceType === 'education'? 10 + rand() * 10
                  : 5 + rand() * 10;
        agent.timeAllocation[instName] = hrs;
      }
    }
  }

  // Build network
  const adjacency = buildAdjacency(nAgents, networkDensity, rand);
  addInstitutionalEdges(adjacency, institutions, agents);

  // History
  const history = { step: [], ...Object.fromEntries(
    Object.keys(PRACTICE_PROFILES).flatMap(p => [
      [`${p}_rate`, []],
      [`${p}_hours`, []],
    ])
  )};

  const model = { agents, institutions, adjacency, history, step: 0,
                  reallocFreq, awarenessRadius, rand };

  recordState(model);
  return model;
}

function recordState(model) {
  const { agents, institutions, history, step } = model;
  history.step.push(step);

  for (const ptype of Object.keys(PRACTICE_PROFILES)) {
    let totalHours = 0, participants = 0;
    for (const agent of agents) {
      let agentHours = 0;
      for (const [name, hrs] of Object.entries(agent.timeAllocation)) {
        if (institutions[name]?.practiceType === ptype) agentHours += hrs;
      }
      totalHours   += agentHours;
      if (agentHours > 0) participants++;
    }
    history[`${ptype}_rate`].push(participants / agents.length);
    history[`${ptype}_hours`].push(totalHours / agents.length);
  }
}

// ── Step ─────────────────────────────────────────────────────────────────────
export function stepModel(model) {
  const { agents, institutions, adjacency, reallocFreq, awarenessRadius, rand } = model;

  // Shuffle agents
  const order = agents.map((_, i) => i).sort(() => rand() - 0.5);

  for (const idx of order) {
    const agent = agents[idx];
    agent.stepsSinceChange++;

    // Learn about institutions from neighbours
    for (const nbrId of (adjacency.get(agent.id) || [])) {
      const nbr = agents[nbrId];
      if (nbr.commStrength >= 0.2) {
        for (const inst of nbr.institutions) agent.awareOf.add(inst);
      }
    }

    // Re-optimise
    if (agent.stepsSinceChange >= reallocFreq) {
      const newAlloc = optimizeAllocation(agent, institutions);

      // Update institution membership
      const oldInsts = new Set(agent.institutions);
      const newInsts = new Set(Object.keys(newAlloc));

      for (const name of oldInsts) {
        if (!newInsts.has(name) && institutions[name]) {
          institutions[name].members.delete(agent.id);
        }
      }
      for (const name of newInsts) {
        if (!oldInsts.has(name) && institutions[name] &&
            institutions[name].members.size < institutions[name].size) {
          institutions[name].members.add(agent.id);
        }
      }

      agent.timeAllocation    = newAlloc;
      agent.institutions      = newInsts;
      agent.stepsSinceChange  = 0;
    }
  }

  // Rebuild institutional network edges
  addInstitutionalEdges(adjacency, institutions, agents);

  model.step++;
  recordState(model);

  return model;
}

// ── Accessors ────────────────────────────────────────────────────────────────
export { getFreeTime, getDominantPractice, PRACTICE_PROFILES };
