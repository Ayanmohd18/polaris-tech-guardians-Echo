import React, { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { motion, AnimatePresence } from 'framer-motion';
import SentientGlass from './components/SentientGlass';
import EchoOrb from './components/EchoOrb';
import PhotonicShift from './components/PhotonicShift';
import AgenticRenderer from './components/AgenticRenderer';
import './App.css';

function App() {
  const [cognitiveState, setCognitiveState] = useState('IDLE');
  const [mode, setMode] = useState('ambient'); // ambient or focus
  const [agentThinking, setAgentThinking] = useState(false);

  useEffect(() => {
    window.updateCognitiveState = (state, data) => {
      setCognitiveState(state);
      setAgentThinking(data.agent_active || false);
    };
  }, []);

  const opacity = cognitiveState === 'FLOWING' ? 0 : 1;
  const glassBlur = cognitiveState === 'FLOWING' ? 0 : cognitiveState === 'STUCK' ? 20 : 10;

  return (
    <div className="bio-hud">
      <Canvas camera={{ position: [0, 0, 5], fov: 50 }}>
        <SentientGlass blur={glassBlur} mode={mode} />
        <EchoOrb state={cognitiveState} thinking={agentThinking} />
        <PhotonicShift mode={mode} />
      </Canvas>

      <motion.div 
        className="ui-chrome"
        animate={{ opacity }}
        transition={{ duration: 0.8 }}
      >
        <div className="ndot-heading">ECHO</div>
        <button onClick={() => setMode(mode === 'ambient' ? 'focus' : 'ambient')}>
          {mode === 'ambient' ? '☀️' : '🌙'}
        </button>
      </motion.div>

      {agentThinking && <AgenticRenderer />}

      {cognitiveState === 'FRUSTRATED' && (
        <div className="glitch-overlay" />
      )}
    </div>
  );
}

export default App;
