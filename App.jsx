import React, { useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import MapView from './components/MapView';
import AgentPanel from './components/AgentPanel';
import ControlBar from './components/ControlBar';
import ResultsDrawer from './components/ResultsDrawer';
import { useSimulation } from './hooks/useSimulation';
import './App.css';

export default function App() {
  const sim = useSimulation();
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [activeTab, setActiveTab] = useState('build'); // 'build' | 'results'

  const handleAgentClick = useCallback((agent) => {
    setSelectedAgent(prev => prev?.id === agent?.id ? null : agent);
  }, []);

  const handleMapClick = useCallback(() => {
    setSelectedAgent(null);
  }, []);

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="app-header__left">
          <span className="app-header__logo">⬡</span>
          <h1 className="app-header__title">Cultural Dynamics</h1>
        </div>
        <div className="app-header__tabs">
          <button
            className={`tab-btn ${activeTab === 'build' ? 'active' : ''}`}
            onClick={() => setActiveTab('build')}
          >Build</button>
          <button
            className={`tab-btn ${activeTab === 'results' ? 'active' : ''}`}
            onClick={() => setActiveTab('results')}
            disabled={!sim.hasRun}
          >Results</button>
        </div>
        <div className="app-header__right">
          {sim.model && (
            <span className="app-header__stat">
              {sim.model.agents.length} agents · {Object.keys(sim.model.institutions).length} institutions · step {sim.currentStep}
            </span>
          )}
        </div>
      </header>

      <div className="app-body">
        {/* Left sidebar */}
        <Sidebar sim={sim} activeTab={activeTab} />

        {/* Main map / results area */}
        <main className="app-main">
          {activeTab === 'build' ? (
            <>
              <ControlBar sim={sim} />
              <MapView
                sim={sim}
                selectedAgent={selectedAgent}
                onAgentClick={handleAgentClick}
                onMapClick={handleMapClick}
              />
            </>
          ) : (
            <ResultsDrawer sim={sim} />
          )}
        </main>

        {/* Right agent inspector panel */}
        {selectedAgent && (
          <AgentPanel
            agent={selectedAgent}
            model={sim.model}
            onClose={() => setSelectedAgent(null)}
          />
        )}
      </div>
    </div>
  );
}
