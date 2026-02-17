import React, { useState } from 'react';
import './ControlBar.css';

export default function ControlBar({ sim }) {
  const [speed, setSpeed] = useState(400); // ms per step

  return (
    <div className="control-bar">
      {/* Init */}
      <button
        className="ctrl-btn primary"
        onClick={sim.initModel}
        disabled={sim.institutions.length === 0}
        title="Initialise model"
      >
        ⬡ Init
      </button>

      <div className="ctrl-divider" />

      {/* Step */}
      <button
        className="ctrl-btn"
        onClick={sim.runStep}
        disabled={!sim.model || sim.isRunning}
        title="Single step"
      >
        ▷ Step
      </button>

      {/* +10 */}
      <button
        className="ctrl-btn"
        onClick={() => sim.runNSteps(10)}
        disabled={!sim.model || sim.isRunning}
        title="Run 10 steps"
      >
        +10
      </button>

      {/* +50 */}
      <button
        className="ctrl-btn"
        onClick={() => sim.runNSteps(50)}
        disabled={!sim.model || sim.isRunning}
        title="Run 50 steps"
      >
        +50
      </button>

      {/* Play/Pause */}
      {sim.isRunning ? (
        <button className="ctrl-btn play active" onClick={sim.stopAnimation} title="Pause">
          ⏸ Pause
        </button>
      ) : (
        <button
          className="ctrl-btn play"
          onClick={() => sim.startAnimation(speed)}
          disabled={!sim.model}
          title="Play animation"
        >
          ▶ Play
        </button>
      )}

      {/* Speed */}
      <label className="speed-control">
        <span>Speed</span>
        <input
          type="range" min={100} max={1000} step={50}
          value={speed}
          onChange={e => setSpeed(+e.target.value)}
          disabled={sim.isRunning}
        />
        <span className="speed-val">{(1000/speed).toFixed(1)}×</span>
      </label>

      <div className="ctrl-divider" />

      {/* Reset */}
      <button
        className="ctrl-btn danger"
        onClick={sim.reset}
        disabled={!sim.model}
        title="Reset simulation"
      >
        ↺ Reset
      </button>

      {/* Step counter */}
      {sim.model && (
        <span className="ctrl-step">
          step <strong>{sim.currentStep}</strong>
        </span>
      )}
    </div>
  );
}
