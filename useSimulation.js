import { useState, useCallback, useRef } from 'react';
import { createModel, stepModel } from '../lib/simulation';

const DEFAULT_VALUES = {
  community: [0.5, 0.2],
  tradition: [0.5, 0.2],
  growth:    [0.5, 0.2],
  civic:     [0.5, 0.2],
  status:    [0.5, 0.2],
  leisure:   [0.5, 0.2],
  wealth:    [0.5, 0.2],
};

export function useSimulation() {
  const [model, setModel]               = useState(null);
  const [currentStep, setCurrentStep]   = useState(0);
  const [isRunning, setIsRunning]       = useState(false);
  const [institutions, setInstitutions] = useState([]);
  const [valueSettings, setValueSettings] = useState(DEFAULT_VALUES);
  const [params, setParams]             = useState({
    nAgents:         80,
    networkDensity:  0.03,
    awarenessRadius: 0.3,
    reallocFreq:     4,
    seed:            42,
  });

  const animFrameRef = useRef(null);
  const modelRef     = useRef(null);

  const initModel = useCallback(() => {
    const m = createModel({
      ...params,
      institutionDefs: institutions,
      valueSettings:   Object.fromEntries(
        Object.entries(valueSettings).map(([k, [mean, std]]) => [k, [mean, std]])
      ),
    });
    modelRef.current = m;
    // Deep-clone for React state (so renders trigger)
    setModel(cloneModel(m));
    setCurrentStep(0);
  }, [params, institutions, valueSettings]);

  const runStep = useCallback(() => {
    if (!modelRef.current) return;
    stepModel(modelRef.current);
    setCurrentStep(modelRef.current.step);
    setModel(cloneModel(modelRef.current));
  }, []);

  const startAnimation = useCallback((speed = 300) => {
    if (!modelRef.current) return;
    setIsRunning(true);

    const tick = () => {
      if (!modelRef.current) return;
      stepModel(modelRef.current);
      setCurrentStep(modelRef.current.step);
      setModel(cloneModel(modelRef.current));
      animFrameRef.current = setTimeout(tick, speed);
    };
    animFrameRef.current = setTimeout(tick, speed);
  }, []);

  const stopAnimation = useCallback(() => {
    setIsRunning(false);
    if (animFrameRef.current) clearTimeout(animFrameRef.current);
  }, []);

  const runNSteps = useCallback((n) => {
    if (!modelRef.current) return;
    for (let i = 0; i < n; i++) stepModel(modelRef.current);
    setCurrentStep(modelRef.current.step);
    setModel(cloneModel(modelRef.current));
  }, []);

  const reset = useCallback(() => {
    stopAnimation();
    modelRef.current = null;
    setModel(null);
    setCurrentStep(0);
  }, [stopAnimation]);

  const addInstitution = useCallback((inst) => {
    setInstitutions(prev => [...prev, inst]);
  }, []);

  const removeInstitution = useCallback((idx) => {
    setInstitutions(prev => prev.filter((_, i) => i !== idx));
  }, []);

  const applyPreset = useCallback((presetValues) => {
    setValueSettings(presetValues);
  }, []);

  return {
    model,
    currentStep,
    isRunning,
    hasRun: currentStep > 0,
    institutions,
    valueSettings,
    params,
    setParams,
    setValueSettings,
    initModel,
    runStep,
    runNSteps,
    startAnimation,
    stopAnimation,
    reset,
    addInstitution,
    removeInstitution,
    applyPreset,
  };
}

// Shallow clone for React — preserves Sets but triggers re-render
function cloneModel(m) {
  return {
    ...m,
    agents:       m.agents.map(a => ({ ...a,
      values:         { ...a.values },
      timeAllocation: { ...a.timeAllocation },
      institutions:   new Set(a.institutions),
      awareOf:        new Set(a.awareOf),
    })),
    institutions: Object.fromEntries(
      Object.entries(m.institutions).map(([k, v]) => [k, { ...v, members: new Set(v.members) }])
    ),
    history: { ...m.history },
    adjacency: m.adjacency,   // keep reference (too large to copy every frame)
  };
}
