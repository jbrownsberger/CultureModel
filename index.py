"""
Cultural Dynamics Simulator - Streamlit App
Interactive web interface for exploring institutional cultural dynamics
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
import json

# Page config
st.set_page_config(
    page_title="Cultural Dynamics Simulator",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'model' not in st.session_state:
    st.session_state.model = None
if 'running' not in st.session_state:
    st.session_state.running = False
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0

# Import model components
from model import CulturalDynamicsModel, Institution, Agent

# CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .institution-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🏛️ Cultural Dynamics Simulator</div>', unsafe_allow_html=True)
st.markdown("**Explore how cultural practices spread through institutional networks**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Model Setup")
    
    # Basic parameters
    with st.expander("🌍 Population", expanded=True):
        n_agents = st.slider(
            "Number of Agents",
            min_value=30,
            max_value=200,
            value=100,
            step=10,
            help="Total number of people in the simulation"
        )
        
        network_density = st.slider(
            "Initial Network Density",
            min_value=0.01,
            max_value=0.15,
            value=0.05,
            step=0.01,
            help="Random connections before institutions (neighbor/family ties)"
        )
    
    # Simulation settings
    with st.expander("⏱️ Simulation", expanded=True):
        max_steps = st.slider(
            "Maximum Steps",
            min_value=10,
            max_value=100,
            value=50,
            step=10
        )
        
        awareness_radius = st.slider(
            "Institution Awareness Radius",
            min_value=0.1,
            max_value=0.5,
            value=0.3,
            step=0.05,
            help="How far institutions broadcast their existence in network space"
        )
        
        reallocation_frequency = st.slider(
            "Reoptimization Frequency",
            min_value=1,
            max_value=10,
            value=4,
            help="How often agents reconsider their time allocation"
        )
    
    # Agent value distributions
    with st.expander("💭 Agent Value Distributions"):
        st.markdown("**Adjust population values:**")
        
        value_settings = {}
        for value_name in ['community', 'tradition', 'growth', 'civic', 'status', 'leisure', 'wealth']:
            col1, col2 = st.columns(2)
            with col1:
                mean = st.slider(
                    f"{value_name.capitalize()} (mean)",
                    0.0, 1.0, 0.5, 0.1,
                    key=f"{value_name}_mean"
                )
            with col2:
                std = st.slider(
                    f"(std dev)",
                    0.0, 0.5, 0.2, 0.05,
                    key=f"{value_name}_std",
                    label_visibility="collapsed"
                )
            value_settings[value_name] = (mean, std)
        
        st.session_state.value_settings = value_settings
    
    st.markdown("---")
    
    # Presets
    st.header("📋 Presets")
    preset = st.selectbox(
        "Load Preset Scenario",
        ["Custom", "Traditional Community", "Secular Urban", "Mixed Values", "Status-Driven"]
    )
    
    if preset != "Custom":
        if st.button("Apply Preset"):
            if preset == "Traditional Community":
                st.session_state.value_settings = {
                    'tradition': (0.8, 0.15),
                    'community': (0.7, 0.2),
                    'growth': (0.4, 0.2),
                    'civic': (0.6, 0.2),
                    'status': (0.3, 0.2),
                    'leisure': (0.5, 0.2),
                    'wealth': (0.4, 0.2),
                }
            elif preset == "Secular Urban":
                st.session_state.value_settings = {
                    'tradition': (0.2, 0.15),
                    'community': (0.4, 0.2),
                    'growth': (0.7, 0.2),
                    'civic': (0.4, 0.2),
                    'status': (0.7, 0.2),
                    'leisure': (0.6, 0.2),
                    'wealth': (0.7, 0.2),
                }
            elif preset == "Status-Driven":
                st.session_state.value_settings = {
                    'tradition': (0.4, 0.2),
                    'community': (0.3, 0.2),
                    'growth': (0.6, 0.2),
                    'civic': (0.3, 0.2),
                    'status': (0.9, 0.1),
                    'leisure': (0.2, 0.2),
                    'wealth': (0.8, 0.15),
                }
            st.success(f"Applied {preset} preset!")
            st.rerun()

# Main area - two tabs
tab1, tab2, tab3, tab4 = st.tabs(["🏗️ Build Model", "📊 Results", "🕸️ Network", "ℹ️ About"])

with tab1:
    st.header("Build Your Cultural System")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Add Institutions")
        st.markdown("Create institutions that will shape cultural dynamics:")
        
        # Institution builder
        with st.form("add_institution"):
            inst_col1, inst_col2, inst_col3 = st.columns(3)
            
            with inst_col1:
                inst_name = st.text_input("Institution Name", "New Institution")
                inst_type = st.selectbox(
                    "Type",
                    ["work", "church", "club", "education", "community_center", "political_org"]
                )
            
            with inst_col2:
                inst_size = st.slider("Max Members", 10, 100, 30)
                money_cost = st.slider("Cost ($/hr)", 0.0, 20.0, 0.0, 0.5)
            
            with inst_col3:
                money_income = st.slider("Income ($/hr)", 0.0, 50.0, 0.0, 5.0)
                
                # Culture sliders
                st.markdown("**Cultural Values:**")
                culture_vals = {}
                for val in ['community', 'tradition', 'growth']:
                    culture_vals[val] = st.slider(
                        val.capitalize(),
                        -1.0, 1.0, 0.0, 0.1,
                        key=f"culture_{val}"
                    )
            
            submitted = st.form_submit_button("➕ Add Institution")
            
            if submitted:
                if 'institutions' not in st.session_state:
                    st.session_state.institutions = []
                
                st.session_state.institutions.append({
                    'name': inst_name,
                    'type': inst_type,
                    'size': inst_size,
                    'money_cost': money_cost,
                    'money_income': money_income,
                    'culture': culture_vals
                })
                st.success(f"Added {inst_name}!")
                st.rerun()
    
    with col2:
        st.subheader("Current Institutions")
        
        if 'institutions' not in st.session_state or len(st.session_state.institutions) == 0:
            st.info("No institutions yet. Add some to get started!")
        else:
            for idx, inst in enumerate(st.session_state.institutions):
                with st.expander(f"{inst['name']} ({inst['type']})"):
                    st.write(f"**Size:** {inst['size']} members")
                    st.write(f"**Cost:** ${inst['money_cost']:.2f}/hr")
                    if inst['money_income'] > 0:
                        st.write(f"**Income:** ${inst['money_income']:.2f}/hr")
                    st.write(f"**Culture:** {inst['culture']}")
                    
                    if st.button("Remove", key=f"remove_{idx}"):
                        st.session_state.institutions.pop(idx)
                        st.rerun()
        
        st.markdown("---")
        
        # Quick add buttons
        st.subheader("Quick Add")
        
        if st.button("+ Add Typical Workplace"):
            if 'institutions' not in st.session_state:
                st.session_state.institutions = []
            st.session_state.institutions.append({
                'name': f'Workplace {len([i for i in st.session_state.institutions if i["type"]=="work"])+1}',
                'type': 'work',
                'size': 40,
                'money_cost': 0,
                'money_income': 25,
                'culture': {'community': 0.3, 'tradition': 0.2, 'growth': 0.4}
            })
            st.rerun()
        
        if st.button("+ Add Church"):
            if 'institutions' not in st.session_state:
                st.session_state.institutions = []
            st.session_state.institutions.append({
                'name': f'Church {len([i for i in st.session_state.institutions if i["type"]=="church"])+1}',
                'type': 'church',
                'size': 30,
                'money_cost': 2,
                'money_income': 0,
                'culture': {'community': 0.8, 'tradition': 0.9, 'growth': 0.3}
            })
            st.rerun()
        
        if st.button("+ Add Club"):
            if 'institutions' not in st.session_state:
                st.session_state.institutions = []
            st.session_state.institutions.append({
                'name': f'Club {len([i for i in st.session_state.institutions if i["type"]=="club"])+1}',
                'type': 'club',
                'size': 25,
                'money_cost': 5,
                'money_income': 0,
                'culture': {'community': 0.6, 'tradition': 0.2, 'growth': 0.5}
            })
            st.rerun()
    
    st.markdown("---")
    
    # Initialize and run
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Initialize Model", type="primary", use_container_width=True):
            if 'institutions' not in st.session_state or len(st.session_state.institutions) == 0:
                st.error("Please add at least one institution first!")
            else:
                with st.spinner("Initializing model..."):
                    # Create model
                    st.session_state.model = CulturalDynamicsModel(
                        n_agents=n_agents,
                        institutions=st.session_state.institutions,
                        value_settings=st.session_state.value_settings,
                        network_density=network_density,
                        awareness_radius=awareness_radius,
                        reallocation_frequency=reallocation_frequency
                    )
                    st.session_state.current_step = 0
                st.success("Model initialized!")
    
    with col2:
        if st.button("▶️ Run Simulation", disabled=st.session_state.model is None, use_container_width=True):
            if st.session_state.model:
                with st.spinner(f"Running {max_steps} steps..."):
                    progress_bar = st.progress(0)
                    for step in range(max_steps):
                        st.session_state.model.step()
                        st.session_state.current_step = step + 1
                        progress_bar.progress((step + 1) / max_steps)
                st.success(f"Completed {max_steps} steps!")
                st.rerun()
    
    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.model = None
            st.session_state.current_step = 0
            st.session_state.institutions = []
            st.rerun()

with tab2:
    st.header("Simulation Results")
    
    if st.session_state.model is None:
        st.info("👈 Initialize a model in the 'Build Model' tab to see results")
    else:
        model = st.session_state.model
        
        # Key metrics
        st.subheader("📈 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_connections = 2 * model.social_network.number_of_edges() / model.n_agents
            st.metric("Avg Social Connections", f"{avg_connections:.1f}")
        
        with col2:
            total_institutions = len(model.institutions)
            st.metric("Total Institutions", total_institutions)
        
        with col3:
            if st.session_state.current_step > 0:
                avg_free_time = np.mean([a.get_free_time() for a in model.agents])
                st.metric("Avg Free Time", f"{avg_free_time:.1f} hrs")
        
        with col4:
            if st.session_state.current_step > 0:
                st.metric("Simulation Step", st.session_state.current_step)
        
        st.markdown("---")
        
        # Time series plots
        if st.session_state.current_step > 0:
            st.subheader("📊 Practice Adoption Over Time")
            
            # Participation rates
            fig = go.Figure()
            
            practice_colors = {
                'work': '#e74c3c',
                'church': '#9b59b6',
                'club': '#3498db',
                'education': '#2ecc71',
                'community_center': '#f39c12',
                'political_org': '#e67e22'
            }
            
            for practice_type in set(inst['type'] for inst in st.session_state.institutions):
                if f'{practice_type}_participation_rate' in model.history:
                    rates = [r * 100 for r in model.history[f'{practice_type}_participation_rate']]
                    fig.add_trace(go.Scatter(
                        x=list(range(len(rates))),
                        y=rates,
                        name=practice_type.replace('_', ' ').title(),
                        line=dict(color=practice_colors.get(practice_type, '#34495e'), width=3),
                        mode='lines+markers'
                    ))
            
            fig.update_layout(
                xaxis_title="Timestep",
                yaxis_title="Participation Rate (%)",
                hovermode='x unified',
                height=400,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Average hours
            st.subheader("⏰ Time Allocation Trends")
            
            fig2 = go.Figure()
            
            for practice_type in set(inst['type'] for inst in st.session_state.institutions):
                if f'{practice_type}_avg_hours' in model.history:
                    fig2.add_trace(go.Scatter(
                        x=list(range(len(model.history[f'{practice_type}_avg_hours']))),
                        y=model.history[f'{practice_type}_avg_hours'],
                        name=practice_type.replace('_', ' ').title(),
                        stackgroup='one',
                    ))
            
            fig2.update_layout(
                xaxis_title="Timestep",
                yaxis_title="Average Hours per Week",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # Institution details
            st.subheader("🏛️ Institution Statistics")
            
            inst_data = []
            for inst_name, inst in model.institutions.items():
                inst_data.append({
                    "Institution": inst.name,
                    "Type": inst.practice_type,
                    "Members": len(inst.members),
                    "Capacity": inst.size,
                    "Utilization": f"{100*len(inst.members)/inst.size:.0f}%",
                    "Avg Hours": f"{np.mean([model.agents[m].time_allocation.get(inst_name, 0) for m in inst.members]):.1f}" if inst.members else "0.0"
                })
            
            df = pd.DataFrame(inst_data)
            st.dataframe(df, use_container_width=True)
            
            # Download data
            st.download_button(
                "📥 Download Results (CSV)",
                df.to_csv(index=False),
                "simulation_results.csv",
                "text/csv"
            )

with tab3:
    st.header("Social Network Visualization")
    
    if st.session_state.model is None:
        st.info("👈 Initialize a model to see the network")
    else:
        model = st.session_state.model
        
        # Network visualization settings
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("Display Options")
            
            color_by = st.radio(
                "Color nodes by:",
                ["Dominant Practice", "Institution Type", "Network Degree"]
            )
            
            show_labels = st.checkbox("Show node labels", False)
            edge_opacity = st.slider("Edge opacity", 0.0, 1.0, 0.2, 0.05)
        
        with col2:
            st.subheader("Network Graph")
            
            # Create network visualization
            pos = nx.spring_layout(model.social_network, seed=42, k=0.3, iterations=50)
            
            # Prepare node colors
            if color_by == "Dominant Practice":
                colors_map = {
                    'work': '#e74c3c', 'church': '#9b59b6', 'club': '#3498db',
                    'education': '#2ecc71', 'community_center': '#f39c12',
                    'political_org': '#e67e22', 'none': '#95a5a6'
                }
                node_colors = [colors_map.get(agent.get_dominant_practice(model.institutions), '#95a5a6')
                              for agent in model.agents]
                legend_title = "Dominant Practice"
            elif color_by == "Institution Type":
                # Color by primary institution
                node_colors = []
                for agent in model.agents:
                    if agent.time_allocation:
                        primary = max(agent.time_allocation.items(), key=lambda x: x[1])[0]
                        if primary in model.institutions:
                            practice = model.institutions[primary].practice_type
                            node_colors.append(colors_map.get(practice, '#95a5a6'))
                        else:
                            node_colors.append('#95a5a6')
                    else:
                        node_colors.append('#95a5a6')
                legend_title = "Primary Institution Type"
            else:  # Network Degree
                degrees = dict(model.social_network.degree())
                max_degree = max(degrees.values()) if degrees else 1
                node_colors = [degrees.get(i, 0) / max_degree for i in range(model.n_agents)]
                legend_title = "Network Degree (normalized)"
            
            # Create plotly figure
            edge_trace = go.Scatter(
                x=[], y=[],
                line=dict(width=0.5, color=f'rgba(125, 125, 125, {edge_opacity})'),
                hoverinfo='none',
                mode='lines'
            )
            
            for edge in model.social_network.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_trace['x'] += tuple([x0, x1, None])
                edge_trace['y'] += tuple([y0, y1, None])
            
            node_trace = go.Scatter(
                x=[pos[i][0] for i in range(model.n_agents)],
                y=[pos[i][1] for i in range(model.n_agents)],
                mode='markers+text' if show_labels else 'markers',
                hoverinfo='text',
                marker=dict(
                    showscale=color_by == "Network Degree",
                    colorscale='Viridis' if color_by == "Network Degree" else None,
                    color=node_colors,
                    size=10,
                    line=dict(width=2, color='white')
                ),
                text=[str(i) if show_labels else None for i in range(model.n_agents)],
                hovertext=[f"Agent {i}<br>Connections: {len(list(model.social_network.neighbors(i)))}"
                          for i in range(model.n_agents)]
            )
            
            fig = go.Figure(data=[edge_trace, node_trace],
                          layout=go.Layout(
                              showlegend=False,
                              hovermode='closest',
                              margin=dict(b=0,l=0,r=0,t=40),
                              xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                              yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                              height=600
                          ))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Network statistics
            st.subheader("Network Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                density = nx.density(model.social_network)
                st.metric("Network Density", f"{density:.3f}")
            
            with col2:
                if nx.is_connected(model.social_network):
                    avg_path_length = nx.average_shortest_path_length(model.social_network)
                    st.metric("Avg Path Length", f"{avg_path_length:.2f}")
                else:
                    st.metric("Avg Path Length", "Disconnected")
            
            with col3:
                clustering = nx.average_clustering(model.social_network)
                st.metric("Clustering Coefficient", f"{clustering:.3f}")

with tab4:
    st.header("About This Simulator")
    
    st.markdown("""
    ### 🎯 What This Models
    
    This simulator explores how **cultural practices spread through institutional networks**.
    
    **Key Dynamics:**
    - 🏢 **Institutions** create social connections between members
    - 👥 **Agents** allocate time based on personal values and constraints
    - 💬 **Awareness** spreads through institutional connections
    - ⚖️ **Optimization** agents maximize utility given time and money constraints
    - 📉 **Diminishing returns** more hours → less marginal benefit
    
    ### 🔬 Theoretical Foundation
    
    Based on research from:
    - **Boyd & Richerson** - Cultural transmission theory
    - **Granovetter** - Strength of weak ties
    - **Putnam** - Social capital and civic engagement
    - **Axelrod** - Cultural dissemination
    - **Centola** - Complex contagion in networks
    
    ### 🛠️ How to Use
    
    1. **Build your model** - Add institutions that shape the cultural landscape
    2. **Set parameters** - Adjust population values and network properties
    3. **Initialize** - Create the agent population and social network
    4. **Run simulation** - Watch practices spread and evolve
    5. **Analyze results** - Examine adoption patterns and network structure
    
    ### 📊 Use Cases
    
    - Study religious participation trends
    - Analyze civic engagement patterns
    - Explore club/association membership dynamics
    - Model workplace culture diffusion
    - Test policy interventions
    
    ### 💡 Tips
    
    - Start with a **simple scenario** (1-2 institution types)
    - Use **presets** to explore different population profiles
    - **Compare scenarios** by saving/loading parameters
    - Watch how **network structure** affects diffusion speed
    - Notice the role of **"bridge" institutions** connecting groups
    
    ### 📚 Learn More
    
    - [GitHub Repository](#) - Source code and documentation
    - [Research Paper](#) - Theoretical background
    - [Tutorial](#) - Step-by-step guide
    
    ---
    
    **Built with:** Python, Streamlit, NetworkX, Plotly
    
    **Version:** 1.0.0
    
    **License:** MIT
    """)
    
    st.info("💡 **Feedback?** This is an active research tool. Contact us with suggestions or bug reports!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    🏛️ Cultural Dynamics Simulator | Built with Streamlit | 
    <a href='https://github.com/yourusername/cultural-dynamics'>GitHub</a>
</div>
""", unsafe_allow_html=True)
