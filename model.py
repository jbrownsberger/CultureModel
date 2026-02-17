"""
Core model for cultural dynamics simulation
Supports dynamic institution placement with locality-based awareness
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Institution:
    """An institution offering a cultural practice"""
    name: str
    practice_type: str
    size: int
    members: Set[int]
    culture: Dict[str, float]
    money_cost_per_hour: float = 0
    money_income_per_hour: float = 0
    position: Tuple[float, float] = (0, 0)  # Position in network space
    
    def __repr__(self):
        return f"{self.name} ({len(self.members)} members)"


class Agent:
    """Agent with values, resources, and institutional memberships"""
    
    def __init__(self, agent_id: int, position: Tuple[float, float] = (0, 0)):
        self.id = agent_id
        self.position = position  # Position in network space
        
        # Values (0-1 scale)
        self.values = {
            'community': np.random.uniform(0, 1),
            'tradition': np.random.uniform(0, 1),
            'growth': np.random.uniform(0, 1),
            'civic': np.random.uniform(0, 1),
            'status': np.random.uniform(0, 1),
            'leisure': np.random.uniform(0, 1),
            'wealth': np.random.uniform(0, 1),
        }
        
        # Resources
        self.time_budget = 168
        self.money_budget = np.random.uniform(500, 2000)
        
        # Allocations
        self.time_allocation: Dict[str, float] = {}
        self.institutions: Set[str] = set()
        self.aware_of: Set[str] = set()
        
        # Communication
        self.communication_strength = np.random.uniform(0.5, 1.0)
        self.timesteps_since_change = 100
    
    def get_total_time_allocated(self) -> float:
        return sum(self.time_allocation.values())
    
    def get_free_time(self) -> float:
        return self.time_budget - self.get_total_time_allocated()
    
    def get_dominant_practice(self, institutions: Dict[str, Institution]) -> str:
        """Get non-work practice where agent spends most time"""
        practice_totals = {}
        for inst_name, hours in self.time_allocation.items():
            if inst_name in institutions:
                practice = institutions[inst_name].practice_type
                if practice != 'work':
                    practice_totals[practice] = practice_totals.get(practice, 0) + hours
        
        return max(practice_totals.items(), key=lambda x: x[1])[0] if practice_totals else 'none'


class CulturalDynamicsModel:
    """
    Main model with dynamic institution placement
    Institutions broadcast awareness to nearby agents
    """
    
    def __init__(
        self,
        n_agents: int,
        institutions: List[Dict],
        value_settings: Dict[str, Tuple[float, float]],
        network_density: float = 0.05,
        awareness_radius: float = 0.3,
        reallocation_frequency: int = 4,
    ):
        self.n_agents = n_agents
        self.awareness_radius = awareness_radius
        self.reallocation_frequency = reallocation_frequency
        
        # Practice profiles
        self.practice_profiles = self._create_practice_profiles()
        
        # Create agents with spatial positions
        self.agents = []
        positions = self._generate_spatial_layout(n_agents)
        for i in range(n_agents):
            agent = Agent(i, positions[i])
            # Set values from distributions
            for value_name, (mean, std) in value_settings.items():
                agent.values[value_name] = np.clip(np.random.normal(mean, std), 0, 1)
            self.agents.append(agent)
        
        # Create institutions from config
        self.institutions: Dict[str, Institution] = {}
        self._create_institutions_from_config(institutions, positions)
        
        # Build initial social network (random connections for neighbors/family)
        self.social_network = self._create_initial_network(network_density)
        
        # Broadcast institution awareness based on proximity
        self._broadcast_institution_awareness()
        
        # Initial memberships
        self._assign_initial_memberships()
        
        # Rebuild network with institutional connections
        self._rebuild_network_with_institutions()
        
        # History
        self.history = {'timestep': []}
        for practice_type in set(self.practice_profiles.keys()):
            self.history[f'{practice_type}_avg_hours'] = []
            self.history[f'{practice_type}_participation_rate'] = []
        
        self.timestep = 0
        self._record_state()
    
    def _generate_spatial_layout(self, n: int) -> List[Tuple[float, float]]:
        """Generate spatial positions for agents"""
        # Use 2D space [0, 1] x [0, 1]
        return [(np.random.random(), np.random.random()) for _ in range(n)]
    
    def _create_practice_profiles(self) -> Dict[str, Dict]:
        """Practice profiles with diminishing returns"""
        return {
            'work': {
                'optimal_hours': 40,
                'diminishing_returns_factor': 1.5,
                'value_benefits_per_hour': {
                    'community': 0.01, 'tradition': 0.0, 'growth': 0.02,
                    'civic': 0.01, 'status': 0.03, 'leisure': -0.05, 'wealth': 0.0,
                }
            },
            'church': {
                'optimal_hours': 10,
                'diminishing_returns_factor': 1.3,
                'value_benefits_per_hour': {
                    'community': 0.15, 'tradition': 0.12, 'growth': 0.05,
                    'civic': 0.06, 'status': 0.04, 'leisure': 0.0, 'wealth': 0.0,
                }
            },
            'club': {
                'optimal_hours': 6,
                'diminishing_returns_factor': 1.4,
                'value_benefits_per_hour': {
                    'community': 0.10, 'tradition': 0.02, 'growth': 0.08,
                    'civic': 0.03, 'status': 0.06, 'leisure': 0.05, 'wealth': 0.0,
                }
            },
            'political_org': {
                'optimal_hours': 15,
                'diminishing_returns_factor': 1.2,
                'value_benefits_per_hour': {
                    'community': 0.07, 'tradition': 0.03, 'growth': 0.06,
                    'civic': 0.15, 'status': 0.09, 'leisure': 0.0, 'wealth': 0.0,
                }
            },
            'education': {
                'optimal_hours': 20,
                'diminishing_returns_factor': 1.1,
                'value_benefits_per_hour': {
                    'community': 0.05, 'tradition': 0.04, 'growth': 0.15,
                    'civic': 0.05, 'status': 0.10, 'leisure': 0.0, 'wealth': 0.0,
                }
            },
            'community_center': {
                'optimal_hours': 30,
                'diminishing_returns_factor': 1.2,
                'value_benefits_per_hour': {
                    'community': 0.12, 'tradition': 0.08, 'growth': 0.04,
                    'civic': 0.02, 'status': 0.02, 'leisure': 0.08, 'wealth': 0.0,
                }
            },
        }
    
    def _create_institutions_from_config(self, inst_configs: List[Dict], agent_positions: List[Tuple[float, float]]):
        """Create institutions from user configuration"""
        for config in inst_configs:
            # Place institution randomly in space
            position = (np.random.random(), np.random.random())
            
            inst_name = f"{config['type']}_{config['name']}"
            self.institutions[inst_name] = Institution(
                name=config['name'],
                practice_type=config['type'],
                size=config['size'],
                members=set(),
                culture=config['culture'],
                money_cost_per_hour=config['money_cost'],
                money_income_per_hour=config['money_income'],
                position=position
            )
    
    def _create_initial_network(self, density: float) -> nx.Graph:
        """Create initial random network (neighbors/family)"""
        return nx.erdos_renyi_graph(self.n_agents, density)
    
    def _broadcast_institution_awareness(self):
        """Institutions broadcast to nearby agents"""
        for inst_name, inst in self.institutions.items():
            for agent in self.agents:
                # Calculate distance
                dist = np.sqrt((agent.position[0] - inst.position[0])**2 +
                             (agent.position[1] - inst.position[1])**2)
                
                # If within awareness radius, agent becomes aware
                if dist <= self.awareness_radius:
                    agent.aware_of.add(inst_name)
    
    def _assign_initial_memberships(self):
        """Agents join institutions they're aware of based on value fit"""
        for agent in self.agents:
            for inst_name in agent.aware_of:
                inst = self.institutions[inst_name]
                
                # Calculate fit
                fit = sum(inst.culture.get(d, 0) * agent.values[d] for d in agent.values)
                
                # Probabilistic membership
                if fit > 0 and np.random.random() < 0.3 and len(inst.members) < inst.size:
                    inst.members.add(agent.id)
                    agent.institutions.add(inst_name)
                    
                    # Initial time allocation
                    if inst.practice_type == 'work':
                        agent.time_allocation[inst_name] = 40
                    elif inst.practice_type == 'church':
                        agent.time_allocation[inst_name] = np.random.uniform(3, 8)
                    elif inst.practice_type == 'club':
                        agent.time_allocation[inst_name] = np.random.uniform(2, 6)
                    elif inst.practice_type == 'education':
                        agent.time_allocation[inst_name] = np.random.uniform(10, 20)
                    else:
                        agent.time_allocation[inst_name] = np.random.uniform(5, 15)
    
    def _rebuild_network_with_institutions(self):
        """Add institutional connections to network"""
        for inst in self.institutions.values():
            members = list(inst.members)
            for i in range(len(members)):
                for j in range(i+1, len(members)):
                    agent_i, agent_j = members[i], members[j]
                    time_i = self.agents[agent_i].time_allocation.get(inst.name, 0)
                    time_j = self.agents[agent_j].time_allocation.get(inst.name, 0)
                    weight = (time_i + time_j) / 2
                    
                    if self.social_network.has_edge(agent_i, agent_j):
                        if 'weight' not in self.social_network[agent_i][agent_j]:
                            self.social_network[agent_i][agent_j]['weight'] = 0
                        self.social_network[agent_i][agent_j]['weight'] += weight
                    else:
                        self.social_network.add_edge(agent_i, agent_j, weight=weight)
    
    def calculate_institution_utility(self, agent: Agent, inst_name: str, hours: float) -> float:
        """Calculate utility for spending hours at an institution"""
        if hours <= 0 or inst_name not in self.institutions:
            return 0
        
        inst = self.institutions[inst_name]
        profile = self.practice_profiles[inst.practice_type]
        
        # Diminishing returns
        dim_factor = profile['diminishing_returns_factor']
        effective_hours = hours ** (1.0 / dim_factor)
        
        # Value benefits
        utility = sum(profile['value_benefits_per_hour'][dim] * agent.values[dim] * effective_hours
                     for dim in agent.values)
        
        # Money
        if inst.practice_type == 'work':
            utility += hours * inst.money_income_per_hour * agent.values['wealth'] * 0.01
        else:
            utility -= hours * inst.money_cost_per_hour * agent.values['wealth'] * 0.01
        
        return utility
    
    def calculate_marginal_utility(self, agent: Agent, inst_name: str, current_hours: float) -> float:
        """Marginal utility of adding one hour"""
        current = self.calculate_institution_utility(agent, inst_name, current_hours)
        new = self.calculate_institution_utility(agent, inst_name, current_hours + 1)
        return new - current
    
    def optimize_allocation(self, agent: Agent) -> Dict[str, float]:
        """Optimize time allocation greedily"""
        allocation = {inst: 0.0 for inst in agent.aware_of}
        time_remaining = agent.time_budget
        
        max_hours = {'work': 60, 'church': 20, 'club': 15, 'political_org': 30,
                    'education': 40, 'community_center': 50}
        
        for _ in range(int(agent.time_budget)):
            if time_remaining <= 0:
                break
            
            marginal_utils = {}
            for inst_name in agent.aware_of:
                if inst_name not in self.institutions:
                    continue
                
                inst = self.institutions[inst_name]
                current_hours = allocation[inst_name]
                max_hrs = max_hours.get(inst.practice_type, 50)
                
                if current_hours >= max_hrs:
                    marginal_utils[inst_name] = -999
                    continue
                
                # Affordability check
                if inst.practice_type != 'work':
                    total_income = sum(allocation.get(i, 0) * self.institutions[i].money_income_per_hour
                                      for i in allocation if i in self.institutions)
                    total_costs = sum(allocation.get(i, 0) * self.institutions[i].money_cost_per_hour
                                     for i in allocation if i in self.institutions)
                    balance = agent.money_budget + total_income - total_costs
                    
                    if balance - inst.money_cost_per_hour < 0:
                        marginal_utils[inst_name] = -999
                        continue
                
                marginal_utils[inst_name] = self.calculate_marginal_utility(agent, inst_name, current_hours)
            
            if not marginal_utils or max(marginal_utils.values()) <= 0.005:
                break
            
            best_inst = max(marginal_utils, key=marginal_utils.get)
            allocation[best_inst] += 1
            time_remaining -= 1
        
        return {i: h for i, h in allocation.items() if h >= 0.5}
    
    def update_awareness(self, agent: Agent):
        """Learn about institutions from network neighbors"""
        for neighbor_id in self.social_network.neighbors(agent.id):
            neighbor = self.agents[neighbor_id]
            if neighbor.communication_strength >= 0.2:
                # Learn about institutions neighbor participates in
                agent.aware_of.update(neighbor.institutions)
    
    def step(self):
        """Execute one timestep"""
        for agent in np.random.permutation(self.agents):
            agent.timesteps_since_change += 1
            self.update_awareness(agent)
            
            if agent.timesteps_since_change >= self.reallocation_frequency:
                new_allocation = self.optimize_allocation(agent)
                
                # Update membership
                old_insts = set(agent.institutions)
                new_insts = set(new_allocation.keys())
                
                # Remove from institutions they left
                for inst_name in old_insts - new_insts:
                    if inst_name in self.institutions:
                        self.institutions[inst_name].members.discard(agent.id)
                
                # Add to new institutions
                for inst_name in new_insts - old_insts:
                    if inst_name in self.institutions and len(self.institutions[inst_name].members) < self.institutions[inst_name].size:
                        self.institutions[inst_name].members.add(agent.id)
                
                agent.time_allocation = new_allocation
                agent.institutions = new_insts
                agent.timesteps_since_change = 0
        
        # Rebuild network connections
        self._rebuild_network_with_institutions()
        
        self._record_state()
        self.timestep += 1
    
    def _record_state(self):
        """Record current state"""
        self.history['timestep'].append(self.timestep)
        
        for practice_type in self.practice_profiles.keys():
            total_hours = sum(
                agent.time_allocation.get(inst_name, 0)
                for agent in self.agents
                for inst_name in agent.time_allocation
                if inst_name in self.institutions 
                and self.institutions[inst_name].practice_type == practice_type
            )
            self.history[f'{practice_type}_avg_hours'].append(total_hours / self.n_agents)
            
            participants = sum(
                1 for agent in self.agents
                if any(inst_name in agent.time_allocation and 
                      inst_name in self.institutions and
                      self.institutions[inst_name].practice_type == practice_type
                      for inst_name in agent.time_allocation)
            )
            self.history[f'{practice_type}_participation_rate'].append(participants / self.n_agents)
