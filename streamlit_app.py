"""
Cultural Dynamics Simulator - Streamlit App
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import networkx as nx

st.set_page_config(
    page_title="Cultural Dynamics Simulator",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from model import CulturalDynamicsModel

# ── Constants ──────────────────────────────────────────────────────────────────

PRACTICE_COLORS = {
    'work':             '#e74c3c',
    'church':           '#9b59b6',
    'club':             '#3498db',
    'education':        '#2ecc71',
    'community_center': '#f39c12',
    'political_org':    '#e67e22',
    'none':             '#bdc3c7',
}

INSTITUTION_SYMBOLS = {
    'work':             'square',
    'church':           'diamond',
    'club':             'star',
    'education':        'triangle-up',
    'community_center': 'pentagon',
    'political_org':    'hexagram',
}

INST_EMOJI = {
    'work': '🏢', 'church': '⛪', 'club': '🎳',
    'education': '🏫', 'political_org': '🏛', 'community_center': '🏡',
}

PRESETS = {
    "Traditional Community": {
        'community': (0.75, 0.15), 'tradition': (0.80, 0.12),
        'growth':    (0.40, 0.20), 'civic':     (0.60, 0.18),
        'status':    (0.30, 0.18), 'leisure':   (0.50, 0.20),
        'wealth':    (0.35, 0.18),
    },
    "Secular Urban": {
        'community': (0.40, 0.20), 'tradition': (0.20, 0.15),
        'growth':    (0.70, 0.18), 'civic':     (0.40, 0.20),
        'status':    (0.70, 0.18), 'leisure':   (0.60, 0.20),
        'wealth':    (0.70, 0.18),
    },
    "Mixed Values": {
        'community': (0.50, 0.25), 'tradition': (0.50, 0.25),
        'growth':    (0.50, 0.25), 'civic':     (0.50, 0.25),
        'status':    (0.50, 0.25), 'leisure':   (0.50, 0.25),
        'wealth':    (0.50, 0.25),
    },
    "Status-Driven": {
        'community': (0.30, 0.18), 'tradition': (0.35, 0.18),
        'growth':    (0.60, 0.18), 'civic':     (0.25, 0.18),
        'status':    (0.90, 0.08), 'leisure':   (0.25, 0.18),
        'wealth':    (0.80, 0.12),
    },
}

# ── Session state defaults ─────────────────────────────────────────────────────

def init_state():
    defaults = {
        'model':          None,
        'current_step':   0,
        'institutions':   [],
        'value_settings': {k: (0.5, 0.2) for k in
                           ['community','tradition','growth','civic','status','leisure','wealth']},
        'network_pos':    None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

# ── Helper: build plotly network figure ───────────────────────────────────────

def build_network_figure(model, color_by, edge_opacity, show_institutions):
    pos = {i: model.agents[i].position for i in range(model.n_agents)}

    # Colors
    if color_by == "Dominant Practice":
        node_colors = [
            PRACTICE_COLORS.get(agent.get_dominant_practice(model.institutions), '#bdc3c7')
            for agent in model.agents
        ]
        use_colorscale = False
    elif color_by == "Primary Institution Type":
        node_colors = []
        for agent in model.agents:
            if agent.time_allocation:
                primary = max(agent.time_allocation.items(), key=lambda x: x[1])[0]
                ptype = model.institutions[primary].practice_type if primary in model.institutions else 'none'
            else:
                ptype = 'none'
            node_colors.append(PRACTICE_COLORS.get(ptype, '#bdc3c7'))
        use_colorscale = False
    else:  # Network Degree
        degrees = dict(model.social_network.degree())
        max_deg = max(degrees.values()) if degrees else 1
        node_colors = [degrees.get(i, 0) / max_deg for i in range(model.n_agents)]
        use_colorscale = True

    # Edges
    ex, ey = [], []
    for u, v in model.social_network.edges():
        ex += [pos[u][0], pos[v][0], None]
        ey += [pos[u][1], pos[v][1], None]

    edge_trace = go.Scatter(
        x=ex, y=ey, mode='lines',
        line=dict(width=0.6, color=f'rgba(150,150,150,{edge_opacity})'),
        hoverinfo='none', showlegend=False,
    )

    # Agent hover text
    hover_texts = []
    for agent in model.agents:
        alloc = sorted(agent.time_allocation.items(), key=lambda x: x[1], reverse=True)
        alloc_str = '<br>'.join(
            f"&nbsp;&nbsp;{model.institutions[n].name if n in model.institutions else n}: {h:.0f} h"
            for n, h in alloc[:4]
        )
        top_vals = sorted(agent.values.items(), key=lambda x: x[1], reverse=True)[:3]
        vals_str = ', '.join(f"{k}: {v:.2f}" for k, v in top_vals)
        hover_texts.append(
            f"<b>Agent {agent.id}</b><br>"
            f"Connections: {model.social_network.degree(agent.id)}<br>"
            f"Free time: {agent.get_free_time():.0f} h<br>"
            f"{alloc_str}<br>"
            f"Top values: {vals_str}"
        )

    node_trace = go.Scatter(
        x=[pos[i][0] for i in range(model.n_agents)],
        y=[pos[i][1] for i in range(model.n_agents)],
        mode='markers',
        marker=dict(
            size=10,
            color=node_colors,
            colorscale='Viridis' if use_colorscale else None,
            showscale=use_colorscale,
            colorbar=dict(title="Degree") if use_colorscale else None,
            line=dict(width=1.5, color='white'),
        ),
        text=hover_texts,
        hovertemplate='%{text}<extra></extra>',
        name='Agents',
    )

    traces = [edge_trace, node_trace]

    # Institution markers
    if show_institutions:
        by_type = {}
        for inst in model.institutions.values():
            by_type.setdefault(inst.practice_type, []).append(inst)

        for ptype, insts in by_type.items():
            ih = [
                f"<b>{inst.name}</b><br>Type: {ptype}<br>"
                f"Members: {len(inst.members)}/{inst.size}<br>"
                f"Cost: ${inst.money_cost_per_hour:.2f}/h | "
                f"Income: ${inst.money_income_per_hour:.2f}/h"
                for inst in insts
            ]
            traces.append(go.Scatter(
                x=[inst.position[0] for inst in insts],
                y=[inst.position[1] for inst in insts],
                mode='markers+text',
                marker=dict(
                    size=24,
                    color=PRACTICE_COLORS.get(ptype, '#555'),
                    symbol=INSTITUTION_SYMBOLS.get(ptype, 'square'),
                    line=dict(width=2.5, color='black'),
                ),
                text=[inst.name for inst in insts],
                textposition='top center',
                textfont=dict(size=9),
                hovertemplate='%{customdata}<extra></extra>',
                customdata=ih,
                name=f"{INST_EMOJI.get(ptype,'')} {ptype.replace('_',' ').title()}",
            ))

    # Practice color legend entries (non-degree mode)
    if not use_colorscale:
        seen = set()
        for agent in model.agents:
            dom = agent.get_dominant_practice(model.institutions)
            if dom not in seen:
                seen.add(dom)
                traces.append(go.Scatter(
                    x=[None], y=[None], mode='markers',
                    marker=dict(size=10, color=PRACTICE_COLORS.get(dom, '#bdc3c7'),
                                symbol='circle'),
                    name=f"● {dom.replace('_',' ').title()}",
                    showlegend=True,
                ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        height=620,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(visible=False, range=[-0.05, 1.05]),
        yaxis=dict(visible=False, range=[-0.05, 1.05]),
        hovermode='closest',
        legend=dict(bgcolor='rgba(255,255,255,0.85)', borderwidth=1, x=1.0),
        plot_bgcolor='#f8f9fa',
    )
    return fig


def build_timeline_figure(model, practice_types, highlight_step=None):
    fig = go.Figure()
    for ptype in practice_types:
        key = f'{ptype}_participation_rate'
        if key not in model.history:
            continue
        rates = [r * 100 for r in model.history[key]]
        fig.add_trace(go.Scatter(
            x=list(range(len(rates))), y=rates,
            name=ptype.replace('_',' ').title(),
            line=dict(color=PRACTICE_COLORS.get(ptype, '#555'), width=2.5),
        ))
    if highlight_step is not None:
        fig.add_vline(x=highlight_step, line_dash='dash', line_color='gray',
                      annotation_text=f'Step {highlight_step}')
    fig.update_layout(
        xaxis_title='Timestep', yaxis_title='Participation (%)',
        hovermode='x unified', height=300,
        margin=dict(t=10, b=40),
        legend=dict(orientation='h', y=1.08),
    )
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("⚙️ Parameters")

    with st.expander("🌍 Population", expanded=True):
        n_agents        = st.slider("Agents", 30, 200, 100, 10)
        network_density = st.slider("Background connection density",
                                    0.01, 0.10, 0.03, 0.01,
                                    help="Random ties (family, neighbours) before institutions")

    with st.expander("⚙️ Simulation"):
        max_steps        = st.slider("Steps to run", 10, 120, 40, 10)
        awareness_radius = st.slider("Institution awareness radius", 0.1, 0.6, 0.3, 0.05,
                                     help="How far in [0,1]² space an institution is visible")
        realloc_freq     = st.slider("Re-optimisation frequency", 1, 10, 4)

    with st.expander("💭 Population Values"):
        preset_choice = st.selectbox("Load preset", ["Custom"] + list(PRESETS.keys()))
        if st.button("Apply preset", disabled=(preset_choice == "Custom")):
            st.session_state.value_settings = dict(PRESETS[preset_choice])
            st.rerun()

        st.caption("Mean (left) and spread (right):")
        new_vs = {}
        for vname, (cm, cs) in st.session_state.value_settings.items():
            c1, c2 = st.columns(2)
            m = c1.slider(vname.capitalize(), 0.0, 1.0, float(cm), 0.05,
                          key=f"vm_{vname}")
            s = c2.slider("±", 0.0, 0.4, float(cs), 0.05,
                          key=f"vs_{vname}", label_visibility="collapsed")
            new_vs[vname] = (m, s)
        st.session_state.value_settings = new_vs

    st.markdown("---")
    if st.button("🗑 Reset everything", use_container_width=True):
        st.session_state.model        = None
        st.session_state.current_step = 0
        st.session_state.institutions = []
        st.session_state.network_pos  = None
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("# 🏛️ Cultural Dynamics Simulator")
st.caption("Explore how practices spread through institutional networks")

tab_build, tab_results, tab_network, tab_about = st.tabs(
    ["🏗️ Build", "📊 Results", "🕸️ Network", "ℹ️ About"]
)

# ── BUILD ─────────────────────────────────────────────────────────────────────
with tab_build:
    st.subheader("Add Institutions")
    left, right = st.columns([3, 2])

    with left:
        with st.form("inst_form", clear_on_submit=True):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                inst_name = st.text_input("Name", "My Institution")
                inst_type = st.selectbox("Type", list(INSTITUTION_SYMBOLS.keys()))
            with fc2:
                inst_size    = st.slider("Max members", 5, 100, 25)
                money_cost   = st.slider("Cost ($/hr)", 0.0, 20.0, 0.0, 0.5)
                money_income = st.slider("Income ($/hr)", 0.0, 50.0, 0.0, 5.0)
            with fc3:
                st.markdown("**Culture signals**")
                culture = {v: st.slider(v.capitalize(), -1.0, 1.0, 0.0, 0.1, key=f"cf_{v}")
                           for v in ['community','tradition','growth','civic','status']}

            if st.form_submit_button("➕ Add institution"):
                st.session_state.institutions.append({
                    'name': inst_name, 'type': inst_type, 'size': inst_size,
                    'money_cost': money_cost, 'money_income': money_income,
                    'culture': dict(culture),
                })
                st.success(f"Added {inst_name}")
                st.rerun()

        st.subheader("Quick-add")
        qa_cols = st.columns(5)
        quick = [
            ("🏢 Workplace",  'work',        40, 0,  25, {'community':0.3,'tradition':0.2,'growth':0.4,'civic':0.2,'status':0.5}),
            ("⛪ Church",     'church',       30, 2,  0,  {'community':0.8,'tradition':0.9,'growth':0.3,'civic':0.5,'status':0.3}),
            ("🎳 Club",       'club',         25, 5,  0,  {'community':0.6,'tradition':0.2,'growth':0.5,'civic':0.3,'status':0.5}),
            ("🏫 School",     'education',    35, 10, 0,  {'community':0.4,'tradition':0.4,'growth':0.9,'civic':0.5,'status':0.7}),
            ("🏛 Civic org",  'political_org',20, 0,  0,  {'community':0.5,'tradition':0.3,'growth':0.4,'civic':0.9,'status':0.4}),
        ]
        for col, (label, qtype, qsize, qcost, qincome, qculture) in zip(qa_cols, quick):
            with col:
                if st.button(label, use_container_width=True):
                    n = sum(1 for i in st.session_state.institutions if i['type']==qtype)+1
                    st.session_state.institutions.append({
                        'name': f"{qtype.replace('_',' ').title()} {n}",
                        'type': qtype, 'size': qsize,
                        'money_cost': qcost, 'money_income': qincome,
                        'culture': qculture,
                    })
                    st.rerun()

    with right:
        st.subheader("Institution list")
        if not st.session_state.institutions:
            st.info("No institutions yet.")
        for idx, inst in enumerate(st.session_state.institutions):
            e = INST_EMOJI.get(inst['type'], '🏛')
            with st.expander(f"{e} {inst['name']}"):
                st.write(f"Type: **{inst['type']}** | Size: **{inst['size']}**")
                st.write(f"Cost: **${inst['money_cost']}/hr** | Income: **${inst['money_income']}/hr**")
                if st.button("Remove", key=f"rm_{idx}"):
                    st.session_state.institutions.pop(idx)
                    st.rerun()

    st.markdown("---")
    rc1, rc2 = st.columns(2)
    with rc1:
        if st.button("🚀 Initialise model", type="primary", use_container_width=True,
                     disabled=len(st.session_state.institutions) == 0):
            with st.spinner("Building model…"):
                st.session_state.network_pos = None
                st.session_state.model = CulturalDynamicsModel(
                    n_agents=n_agents,
                    institutions=st.session_state.institutions,
                    value_settings=st.session_state.value_settings,
                    network_density=network_density,
                    awareness_radius=awareness_radius,
                    reallocation_frequency=realloc_freq,
                )
                st.session_state.current_step = 0
            st.success("Model ready — head to Results or Network tabs.")
    with rc2:
        if st.button("▶️ Run simulation", use_container_width=True,
                     disabled=st.session_state.model is None):
            with st.spinner(f"Running {max_steps} steps…"):
                bar = st.progress(0)
                for s in range(max_steps):
                    st.session_state.model.step()
                    st.session_state.current_step = s + 1
                    bar.progress((s + 1) / max_steps)
            st.success("Done!")
            st.rerun()

# ── RESULTS ───────────────────────────────────────────────────────────────────
with tab_results:
    if st.session_state.model is None:
        st.info("👈 Build and run a model first.")
    else:
        model = st.session_state.model
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Agents", model.n_agents)
        m2.metric("Institutions", len(model.institutions))
        m3.metric("Connections", model.social_network.number_of_edges())
        m4.metric("Steps run", st.session_state.current_step)
        st.markdown("---")

        practice_types = list({inst['type'] for inst in st.session_state.institutions})

        if st.session_state.current_step > 0:
            st.subheader("Participation rates over time")
            st.plotly_chart(build_timeline_figure(model, practice_types),
                            use_container_width=True)

            st.subheader("Average hours per week")
            fig_h = go.Figure()
            for ptype in practice_types:
                key = f'{ptype}_avg_hours'
                if key in model.history:
                    fig_h.add_trace(go.Scatter(
                        x=list(range(len(model.history[key]))),
                        y=model.history[key],
                        name=ptype.replace('_',' ').title(),
                        stackgroup='one',
                        line=dict(color=PRACTICE_COLORS.get(ptype,'#555')),
                    ))
            fig_h.update_layout(height=320, hovermode='x unified',
                                xaxis_title='Step', yaxis_title='Avg hrs/week',
                                margin=dict(t=10, b=40))
            st.plotly_chart(fig_h, use_container_width=True)

        st.subheader("Institution statistics")
        rows = []
        for iname, inst in model.institutions.items():
            avg_h = (np.mean([model.agents[m].time_allocation.get(iname, 0)
                              for m in inst.members]) if inst.members else 0)
            rows.append({
                "Institution": inst.name, "Type": inst.practice_type,
                "Members": len(inst.members), "Capacity": inst.size,
                "Fill %": f"{100*len(inst.members)/inst.size:.0f}",
                "Avg hrs/wk": f"{avg_h:.1f}",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("📥 Download CSV", df.to_csv(index=False),
                           "results.csv", "text/csv")

# ── NETWORK ───────────────────────────────────────────────────────────────────
with tab_network:
    if st.session_state.model is None:
        st.info("👈 Build a model first.")
    else:
        model = st.session_state.model

        opt_col, _ = st.columns([1, 3])
        with opt_col:
            color_by     = st.radio("Colour agents by",
                ["Dominant Practice", "Primary Institution Type", "Network Degree"])
            edge_opacity = st.slider("Edge opacity", 0.0, 1.0, 0.15, 0.05)
            show_insts   = st.checkbox("Show institutions", value=True)

        if st.session_state.current_step > 0:
            st.subheader("Participation timeline")
            practice_types = list({inst['type'] for inst in st.session_state.institutions})
            view_step = st.slider("Scrub through time ↔",
                                  0, st.session_state.current_step,
                                  st.session_state.current_step,
                                  key="tl_scrub")
            st.plotly_chart(
                build_timeline_figure(model, practice_types, highlight_step=view_step),
                use_container_width=True,
            )

        st.subheader("Network map")
        st.caption("Small circles = agents (coloured by practice). "
                   "Large shapes = institutions. Hover anything for details.")
        st.plotly_chart(
            build_network_figure(model, color_by, edge_opacity, show_insts),
            use_container_width=True,
        )

        s1, s2, s3 = st.columns(3)
        s1.metric("Density", f"{nx.density(model.social_network):.4f}")
        s2.metric("Avg clustering", f"{nx.average_clustering(model.social_network):.3f}")
        s3.metric("Connected", "Yes" if nx.is_connected(model.social_network) else "No")

# ── ABOUT ─────────────────────────────────────────────────────────────────────
with tab_about:
    st.markdown("""
## 🎯 What This Models

Agents live in a shared 2-D space alongside **institutions** (workplaces, churches, clubs…).
Institutions *broadcast awareness* to any agent within a configurable radius; agents join
based on value fit, allocate time using **marginal-utility optimisation**, and spread
awareness of other institutions to their co-members.

### Key mechanics

| Mechanic | Description |
|---|---|
| Spatial layout | Agents and institutions placed in [0,1]² |
| Awareness radius | Institution visible only within radius |
| Network formation | Social ties form through co-membership |
| Time allocation | Greedy 168 h/week optimisation |
| Diminishing returns | Extra hours yield less benefit |
| Cultural diffusion | Co-members share institutional awareness |

### Theoretical roots
Boyd & Richerson · Granovetter · Putnam · Axelrod · Centola

### Tips
- Start with 2–3 institution types, run 30–50 steps
- Use **Awareness radius** to model rural (small reach) vs urban (large reach)
- Toggle **Show institutions** in the Network tab to see them on the spatial map
- Use the **timeline scrubber** to mark a point on the participation chart
- Try different **presets** to compare traditional vs secular populations
    """)
