import React, { useState, useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { motion, AnimatePresence } from 'framer-motion';
import { SentientGlass } from './components/SentientGlass';
import { EchoOrb } from './components/EchoOrb';
import { NeuralNetwork } from './components/NeuralNetwork';
import { BioCognitiveHUD } from './components/BioCognitiveHUD';
import { PhotonicShift } from './components/PhotonicShift';
import axios from 'axios';
import './App.css';

const API_BASE = window.location.origin;

function App() {
  const [cognitiveState, setCognitiveState] = useState('IDLE');
  const [teamStates, setTeamStates] = useState({});
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [ambientMode, setAmbientMode] = useState(true);
  const [agentThinking, setAgentThinking] = useState(false);
  const [lastUpdate, setLastUpdate] = useState('--');
  const [sessionStart] = useState(new Date());
  const [sessionTime, setSessionTime] = useState('00:00:00');
  const [ws, setWs] = useState(null);
  const [logs, setLogs] = useState([]);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  
  const userId = 'developer_001';
  const canvasRef = useRef();

  // Mouse tracking for parallax
  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 2 - 1,
        y: -(e.clientY / window.innerHeight) * 2 + 1
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Session time tracker
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      const diff = Math.floor((now - sessionStart) / 1000);
      const hours = Math.floor(diff / 3600);
      const minutes = Math.floor((diff % 3600) / 60);
      const seconds = diff % 60;
      
      setSessionTime(
        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
      );
    }, 1000);

    return () => clearInterval(timer);
  }, [sessionStart]);

  // WebSocket connection for real-time cognitive state
  useEffect(() => {
    const connectWebSocket = () => {
      const websocket = new WebSocket(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/${userId}`);
      
      websocket.onopen = () => {
        console.log('🧠 Neural link established');
        addLog('Neural link established');
      };
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'state_update') {
          setCognitiveState(data.state);
          setLastUpdate(new Date().toLocaleTimeString());
          setTeamStates(data.team_states || {});
          addLog(`Cognitive state: ${data.state}`);
          
          // Trigger glitch effect for frustration
          if (data.state === 'FRUSTRATED') {
            triggerGlitchEffect();
          }
        }
      };
      
      websocket.onclose = () => {
        console.log('Neural link disconnected');
        addLog('Neural link disconnected - reconnecting...');
        setTimeout(connectWebSocket, 3000);
      };
      
      setWs(websocket);
    };

    connectWebSocket();
    return () => ws?.close();
  }, [userId]);

  const addLog = (message) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev.slice(-9), `[${timestamp}] ${message}`]);
  };

  const triggerGlitchEffect = () => {
    document.body.classList.add('glitch-effect');
    setTimeout(() => {
      document.body.classList.remove('glitch-effect');
    }, 200);
  };

  const startMonitoring = async () => {
    setAgentThinking(true);
    try {
      const response = await axios.post(`${API_BASE}/api/start/${userId}`);
      if (response.data.status === 'started' || response.data.status === 'already_running') {
        setIsMonitoring(true);
        addLog('Bio-cognitive monitoring initiated');
      }
    } catch (error) {
      console.error('Failed to start monitoring:', error);
      addLog('Neural link failed to establish');
    }
    setAgentThinking(false);
  };

  const stopMonitoring = async () => {
    setAgentThinking(true);
    try {
      const response = await axios.post(`${API_BASE}/api/stop/${userId}`);
      if (response.data.status === 'stopped' || response.data.status === 'not_running') {
        setIsMonitoring(false);
        setCognitiveState('OFFLINE');
        addLog('Bio-cognitive monitoring terminated');
      }
    } catch (error) {
      console.error('Failed to stop monitoring:', error);
      addLog('Neural link termination failed');
    }
    setAgentThinking(false);
  };

  const togglePhotonicShift = () => {
    setAmbientMode(!ambientMode);
    addLog(`Photonic shift: ${ambientMode ? 'FOCUS' : 'AMBIENT'} mode`);
  };

  // Bio-reactive opacity based on cognitive state
  const getInterfaceOpacity = () => {
    switch (cognitiveState) {
      case 'FLOWING': return 0.1; // Nearly invisible during flow
      case 'STUCK': return 0.7;   // More visible when stuck
      case 'FRUSTRATED': return 0.8; // Fully visible when frustrated
      case 'IDLE': return 0.6;    // Moderate visibility when idle
      default: return 0.6;
    }
  };

  const getGlassBlur = () => {
    switch (cognitiveState) {
      case 'FLOWING': return 0;    // No blur during flow
      case 'STUCK': return 20;     // Increased blur when stuck
      case 'FRUSTRATED': return 15; // Moderate blur when frustrated
      case 'IDLE': return 10;      // Light blur when idle
      default: return 10;
    }
  };

  return (
    <div className={`bio-cognitive-hud ${ambientMode ? 'ambient-mode' : 'focus-mode'}`}>
      {/* Three.js Canvas for 3D Sentient Glass */}
      <Canvas
        ref={canvasRef}
        className="sentient-canvas"
        camera={{ position: [0, 0, 5], fov: 75 }}
      >
        <SentientGlass 
          cognitiveState={cognitiveState}
          mousePosition={mousePosition}
          ambientMode={ambientMode}
          blur={getGlassBlur()}
        />
        <EchoOrb 
          cognitiveState={cognitiveState}
          isThinking={agentThinking}
          ambientMode={ambientMode}
        />
        <PhotonicShift ambientMode={ambientMode} />
        {agentThinking && <NeuralNetwork />}
      </Canvas>

      {/* Bio-Cognitive HUD Overlay */}
      <motion.div 
        className="hud-overlay"
        animate={{ 
          opacity: getInterfaceOpacity(),
          backdropFilter: `blur(${getGlassBlur()}px)`
        }}
        transition={{ duration: 0.8, ease: "easeInOut" }}
      >
        <BioCognitiveHUD
          userId={userId}
          cognitiveState={cognitiveState}
          teamStates={teamStates}
          isMonitoring={isMonitoring}
          sessionTime={sessionTime}
          lastUpdate={lastUpdate}
          logs={logs}
          ambientMode={ambientMode}
          onStartMonitoring={startMonitoring}
          onStopMonitoring={stopMonitoring}
          onPhotonicShift={togglePhotonicShift}
          agentThinking={agentThinking}
        />
      </motion.div>

      {/* Ndot57 Typography Test */}
      <div className="ndot57-showcase">
        <h1 className="ndot57-title">ECHO</h1>
        <p className="ndot57-subtitle">OMNISCIENT CREATIVE ENVIRONMENT</p>
      </div>

      {/* Glitch Effect Overlay */}
      <div className="glitch-overlay"></div>
    </div>
  );
}

export default App;