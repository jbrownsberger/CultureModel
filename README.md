# Cultural Dynamics Simulator — React App

Interactive agent-based model of how cultural practices spread through institutional networks.

## Live Demo

Deploy to Vercel or Netlify in one click — no backend required. The entire simulation runs in the browser.

---

## Quick Start

```bash
cd react_app
npm install
npm start
```

Opens at `http://localhost:3000`

---

## Deploy to Vercel (recommended — free)

1. Push this repo to GitHub
2. Go to [vercel.com](https://vercel.com) → New Project
3. Import your repo
4. Set **Root Directory** to `react_app`
5. Click Deploy — done in ~90 seconds

Or via CLI:
```bash
npm install -g vercel
cd react_app
vercel
```

## Deploy to Netlify

1. Go to [netlify.com](https://netlify.com) → Add new site → Import from Git
2. Set **Base directory**: `react_app`
3. Set **Build command**: `npm run build`
4. Set **Publish directory**: `react_app/build`
5. Deploy

---

## How to Use

### 1 — Add Institutions
Use the **quick-add buttons** (Workplace, Church, Club…) or define a custom institution with name, type, capacity, cost, income, and cultural values.

### 2 — Set Population
In the **Population** tab, adjust the mean and spread of each value dimension. Use **presets** (Traditional, Secular Urban, Status-Driven) to quickly test different scenarios.

### 3 — Adjust Parameters
- **Agents** — population size (30–200)
- **Awareness radius** — how far institutions broadcast
- **Background density** — random pre-institutional ties (family, neighbours)
- **Reoptimise every N steps** — how often agents recalculate their time allocation

### 4 — Run
- **Init** — creates the agent population and social network
- **Step** — one timestep
- **+10 / +50** — batch steps
- **Play** — animate in real-time with adjustable speed

### 5 — Inspect
- **Click any agent** (circle) to open the Agent Inspector panel showing time allocation, values, connections, and institutional awareness
- **Hover agents** for a quick tooltip
- **Hover institutions** (larger shapes) to see membership stats
- Switch to the **Results** tab to see charts

---

## Architecture

```
react_app/
├── src/
│   ├── lib/
│   │   └── simulation.js     # All model logic (agents, institutions, network, optimisation)
│   ├── hooks/
│   │   └── useSimulation.js  # React state wrapper for the model
│   ├── components/
│   │   ├── MapView.jsx        # SVG spatial visualisation
│   │   ├── Sidebar.jsx        # Institution builder + parameter controls
│   │   ├── ControlBar.jsx     # Play/pause/step controls
│   │   ├── AgentPanel.jsx     # Click-to-inspect agent detail panel
│   │   └── ResultsDrawer.jsx  # Charts and statistics
│   ├── App.jsx                # Top-level layout
│   └── index.css              # Design system (CSS variables, fonts)
└── package.json
```

The model is a pure JavaScript port of the Python simulation — no server needed.

---

## Model Overview

**Agents** are placed randomly in a 2D space [0,1]². Each has personal values (community, tradition, growth, civic, status, leisure, wealth), a time budget of 168 h/week, and a money budget.

**Institutions** (workplaces, churches, clubs, schools, civic orgs) also have positions. On initialisation they **broadcast awareness** to all agents within the awareness radius. Agents join institutions based on value fit, then connect socially through co-membership.

Each step:
1. Agents learn about new institutions from their network neighbours
2. Every N steps, agents **reoptimise** their time allocation using a greedy marginal-utility algorithm with diminishing returns
3. Social connections update to reflect current memberships

---

## Extending

**Add a new institution type:**
```js
// In src/lib/simulation.js, add to PRACTICE_PROFILES:
my_type: {
  optimalHours: 10,
  dr: 1.3,  // diminishing returns factor
  benefits: { community: 0.1, tradition: 0.0, ... }
}

// Add to PRACTICE_COLORS, INSTITUTION_ICONS, INST_SHAPES, MAX_HOURS
```

**Add a new agent value:**
```js
// In createAgent(), add to agent.values
// In applyValueSettings(), it will be applied automatically
// Add to Sidebar.jsx PRESETS if desired
```

---

## License

MIT
