import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export function BioCognitiveHUD({
  userId,
  cognitiveState,
  teamStates,
  isMonitoring,
  sessionTime,
  lastUpdate,
  logs,
  ambientMode,
  onStartMonitoring,
  onStopMonitoring,
  onPhotonicShift,
  agentThinking
}) {
  
  const getCognitiveStateDescription = (state) => {
    const descriptions = {
      FLOWING: 'Neural pathways optimized • Deep focus achieved',
      STUCK: 'Cognitive processing • Seeking new perspectives',
      FRUSTRATED: 'Stress patterns detected • Recalibrating approach',
      IDLE: 'Baseline monitoring • Ready for engagement',
      OFFLINE: 'Neural link terminated • Standby mode'
    };
    return descriptions[state] || 'Unknown cognitive pattern';
  };

  const teamMembers = Object.entries(teamStates).filter(([id]) => id !== userId);

  return (
    <div className={`bio-cognitive-interface cognitive-state-${cognitiveState.toLowerCase()}`}>
      
      {/* Primary HUD - Top Left */}
      <motion.div 
        className="hud-component primary-hud"
        style={{
          position: 'absolute',
          top: '80px',
          left: '20px',
          minWidth: '320px'
        }}
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <div className="ndot57-text" style={{ fontSize: '1.2rem', marginBottom: '10px' }}>
          COGNITIVE STATUS
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '15px' }}>
          <div className={`cognitive-indicator ${cognitiveState.toLowerCase()}`}></div>
          <div>
            <div className="ndot57-text" style={{ fontSize: '1.5rem', marginBottom: '5px' }}>
              {cognitiveState}
            </div>
            <div className="bio-reactive-text" style={{ fontSize: '0.9rem', opacity: 0.8 }}>
              {getCognitiveStateDescription(cognitiveState)}
            </div>
          </div>
        </div>

        <div className="bio-reactive-text" style={{ fontSize: '0.8rem', opacity: 0.7 }}>
          <div>USER: {userId}</div>
          <div>SESSION: {sessionTime}</div>
          <div>LAST UPDATE: {lastUpdate}</div>
        </div>
      </motion.div>

      {/* Control Panel - Top Right */}
      <motion.div 
        className="hud-component control-panel"
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          display: 'flex',
          gap: '10px',
          flexDirection: 'column'
        }}
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
      >
        <button
          className={`bio-button ${isMonitoring ? 'danger' : 'primary'}`}
          onClick={isMonitoring ? onStopMonitoring : onStartMonitoring}
          disabled={agentThinking}
        >
          {agentThinking ? 'PROCESSING...' : (isMonitoring ? 'TERMINATE LINK' : 'INITIATE NEURAL LINK')}
        </button>
        
        <button
          className="bio-button photonic"
          onClick={onPhotonicShift}
        >
          PHOTONIC SHIFT
        </button>
      </motion.div>

      {/* Team Flow States - Right Side */}
      <AnimatePresence>
        {teamMembers.length > 0 && (
          <motion.div 
            className="hud-component team-flow-panel"
            style={{
              position: 'absolute',
              top: '50%',
              right: '20px',
              transform: 'translateY(-50%)',
              minWidth: '250px'
            }}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 50 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.4 }}
          >
            <div className="ndot57-text" style={{ fontSize: '1rem', marginBottom: '15px' }}>
              TEAM NEURAL NETWORK
            </div>
            
            {teamMembers.map(([memberId, memberData]) => (
              <motion.div 
                key={memberId}
                className="team-member-status"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '10px',
                  padding: '8px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  borderRadius: '6px'
                }}
                whileHover={{ x: 5, background: 'rgba(255, 255, 255, 0.1)' }}
              >
                <div className={`cognitive-indicator ${memberData.state.toLowerCase()}`}></div>
                <div>
                  <div className="ndot57-text" style={{ fontSize: '0.9rem' }}>
                    {memberId.toUpperCase()}
                  </div>
                  <div className="bio-reactive-text" style={{ fontSize: '0.7rem', opacity: 0.7 }}>
                    {memberData.state} • {memberData.simulated ? 'SIM' : 'LIVE'}
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Activity Log - Bottom */}
      <motion.div 
        className="hud-component activity-log"
        style={{
          position: 'absolute',
          bottom: '20px',
          left: '20px',
          right: '20px',
          maxHeight: '150px'
        }}
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut", delay: 0.6 }}
      >
        <div className="ndot57-text" style={{ fontSize: '0.9rem', marginBottom: '10px' }}>
          NEURAL ACTIVITY LOG
        </div>
        
        <div 
          className="log-stream bio-reactive-text"
          style={{
            maxHeight: '100px',
            overflowY: 'auto',
            fontSize: '0.8rem',
            fontFamily: 'Courier New, monospace',
            lineHeight: '1.4'
          }}
        >
          {logs.map((log, index) => (
            <motion.div 
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: index === logs.length - 1 ? 1 : 0.7, x: 0 }}
              transition={{ duration: 0.3 }}
              style={{
                marginBottom: '2px',
                color: index === logs.length - 1 ? '#00ffff' : 'inherit'
              }}
            >
              {log}
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Agent Thinking Indicator */}
      <AnimatePresence>
        {agentThinking && (
          <motion.div
            className="agent-thinking-indicator"
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              pointerEvents: 'none'
            }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.5 }}
          >
            <div className="ndot57-text" style={{ fontSize: '1.5rem', marginBottom: '10px' }}>
              NEURAL PROCESSING
            </div>
            <div className="bio-reactive-text" style={{ fontSize: '0.9rem', opacity: 0.8 }}>
              Cognitive algorithms active • Pattern synthesis in progress
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Cognitive State Descriptions - Hidden during flow */}
      <AnimatePresence>
        {cognitiveState !== 'FLOWING' && (
          <motion.div 
            className="hud-component state-descriptions"
            style={{
              position: 'absolute',
              bottom: '200px',
              right: '20px',
              maxWidth: '300px'
            }}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 50 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.8 }}
          >
            <div className="ndot57-text" style={{ fontSize: '0.8rem', marginBottom: '10px' }}>
              COGNITIVE PATTERNS
            </div>
            
            {[
              { state: 'FLOWING', desc: 'Optimal neural efficiency' },
              { state: 'STUCK', desc: 'Processing complex patterns' },
              { state: 'FRUSTRATED', desc: 'Stress response detected' },
              { state: 'IDLE', desc: 'Baseline consciousness' }
            ].map(({ state, desc }) => (
              <div 
                key={state}
                className="bio-reactive-text"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '5px',
                  fontSize: '0.7rem',
                  opacity: cognitiveState === state ? 1 : 0.5
                }}
              >
                <div className={`cognitive-indicator ${state.toLowerCase()}`} style={{ marginRight: '8px' }}></div>
                <span style={{ marginRight: '10px', fontWeight: 'bold' }}>{state}</span>
                <span>{desc}</span>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}