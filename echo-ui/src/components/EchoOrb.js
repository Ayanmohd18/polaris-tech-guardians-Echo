import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere } from '@react-three/drei';
import * as THREE from 'three';

export function EchoOrb({ cognitiveState, isThinking, ambientMode }) {
  const orbRef = useRef();
  const lightRef = useRef();
  const particlesRef = useRef();

  // Create particle system for thinking visualization
  const particles = useMemo(() => {
    const particleCount = 50;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    
    for (let i = 0; i < particleCount; i++) {
      // Create constellation pattern around orb
      const radius = 1.5 + Math.random() * 2;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);
      
      // Ndot57-style colors (white/blue)
      colors[i * 3] = 1;     // R
      colors[i * 3 + 1] = 1; // G
      colors[i * 3 + 2] = 1; // B
    }
    
    return { positions, colors, count: particleCount };
  }, []);

  // Get orb properties based on cognitive state
  const getOrbProperties = (state) => {
    switch (state) {
      case 'FLOWING':
        return {
          color: '#4CAF50',
          intensity: 0.5,
          scale: 0.8,
          pulseSpeed: 2,
          lightIntensity: 1
        };
      case 'STUCK':
        return {
          color: '#2196F3',
          intensity: 0.8,
          scale: 1,
          pulseSpeed: 1,
          lightIntensity: 1.5
        };
      case 'FRUSTRATED':
        return {
          color: '#FF9800',
          intensity: 1,
          scale: 1.2,
          pulseSpeed: 4,
          lightIntensity: 2
        };
      case 'IDLE':
        return {
          color: '#9E9E9E',
          intensity: 0.6,
          scale: 0.9,
          pulseSpeed: 0.5,
          lightIntensity: 0.8
        };
      default:
        return {
          color: '#9E9E9E',
          intensity: 0.6,
          scale: 0.9,
          pulseSpeed: 0.5,
          lightIntensity: 0.8
        };
    }
  };

  useFrame((state, delta) => {
    const time = state.clock.getElapsedTime();
    const props = getOrbProperties(cognitiveState);
    
    if (orbRef.current) {
      // Pulsing animation
      const pulse = Math.sin(time * props.pulseSpeed) * 0.1 + 1;
      orbRef.current.scale.setScalar(props.scale * pulse);
      
      // Gentle floating motion
      orbRef.current.position.y = Math.sin(time * 0.5) * 0.1;
      orbRef.current.rotation.y += delta * 0.2;
      
      // Frustration shake effect
      if (cognitiveState === 'FRUSTRATED') {
        orbRef.current.position.x = (Math.random() - 0.5) * 0.05;
        orbRef.current.position.z = (Math.random() - 0.5) * 0.05;
      } else {
        orbRef.current.position.x = THREE.MathUtils.lerp(orbRef.current.position.x, 0, delta * 5);
        orbRef.current.position.z = THREE.MathUtils.lerp(orbRef.current.position.z, 0, delta * 5);
      }
    }
    
    // Update light properties
    if (lightRef.current) {
      lightRef.current.intensity = props.lightIntensity * (Math.sin(time * props.pulseSpeed) * 0.3 + 0.7);
      lightRef.current.color.setHex(props.color.replace('#', '0x'));
    }
    
    // Animate thinking particles
    if (particlesRef.current && isThinking) {
      const positions = particlesRef.current.geometry.attributes.position.array;
      
      for (let i = 0; i < particles.count; i++) {
        const i3 = i * 3;
        
        // Rotate particles around orb
        const radius = Math.sqrt(positions[i3] ** 2 + positions[i3 + 1] ** 2 + positions[i3 + 2] ** 2);
        const angle = Math.atan2(positions[i3 + 1], positions[i3]) + delta * 0.5;
        
        positions[i3] = radius * Math.cos(angle);
        positions[i3 + 1] = radius * Math.sin(angle);
        
        // Pulsing effect
        const pulse = Math.sin(time * 2 + i * 0.1) * 0.1 + 0.9;
        positions[i3] *= pulse;
        positions[i3 + 1] *= pulse;
        positions[i3 + 2] *= pulse;
      }
      
      particlesRef.current.geometry.attributes.position.needsUpdate = true;
    }
  });

  const orbProps = getOrbProperties(cognitiveState);

  return (
    <group position={[2, 1, 0]}>
      {/* Main ECHO Orb */}
      <Sphere ref={orbRef} args={[0.3, 32, 32]} position={[0, 0, 0]}>
        <meshPhysicalMaterial
          color={orbProps.color}
          emissive={orbProps.color}
          emissiveIntensity={orbProps.intensity * 0.3}
          roughness={0.1}
          metalness={0.1}
          transmission={0.2}
          transparent={true}
          opacity={0.8}
        />
      </Sphere>
      
      {/* Dynamic Point Light */}
      <pointLight
        ref={lightRef}
        position={[0, 0, 0]}
        intensity={orbProps.lightIntensity}
        color={orbProps.color}
        distance={10}
        decay={2}
      />
      
      {/* Thinking Particles (Neural Network Visualization) */}
      {isThinking && (
        <points ref={particlesRef}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={particles.count}
              array={particles.positions}
              itemSize={3}
            />
            <bufferAttribute
              attach="attributes-color"
              count={particles.count}
              array={particles.colors}
              itemSize={3}
            />
          </bufferGeometry>
          <pointsMaterial
            size={0.05}
            vertexColors={true}
            transparent={true}
            opacity={0.8}
            sizeAttenuation={true}
          />
        </points>
      )}
    </group>
  );
}