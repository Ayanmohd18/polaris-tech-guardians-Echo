import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Plane } from '@react-three/drei';
import * as THREE from 'three';

export function SentientGlass({ cognitiveState, mousePosition, ambientMode, blur }) {
  const glass1Ref = useRef();
  const glass2Ref = useRef();
  const glass3Ref = useRef();
  const glass4Ref = useRef();

  // Create glass material with dynamic properties
  const glassMaterial = useMemo(() => {
    return new THREE.MeshPhysicalMaterial({
      transmission: 0.9,
      opacity: 0.1,
      roughness: 0.1,
      thickness: 0.5,
      envMapIntensity: 1.5,
      clearcoat: 1,
      clearcoatRoughness: 0.1,
      transparent: true,
      side: THREE.DoubleSide,
    });
  }, []);

  // Animate glass panes based on cognitive state and mouse position
  useFrame((state, delta) => {
    const time = state.clock.getElapsedTime();
    
    // Parallax effect based on mouse position
    const parallaxStrength = cognitiveState === 'FLOWING' ? 0.02 : 0.05;
    
    if (glass1Ref.current) {
      glass1Ref.current.position.x = mousePosition.x * parallaxStrength;
      glass1Ref.current.position.y = mousePosition.y * parallaxStrength * 0.5;
      glass1Ref.current.rotation.y = Math.sin(time * 0.5) * 0.02;
    }
    
    if (glass2Ref.current) {
      glass2Ref.current.position.x = mousePosition.x * parallaxStrength * 0.7;
      glass2Ref.current.position.y = mousePosition.y * parallaxStrength * 0.3;
      glass2Ref.current.position.z = -0.5 + Math.sin(time * 0.3) * 0.1;
    }
    
    if (glass3Ref.current) {
      glass3Ref.current.position.x = mousePosition.x * parallaxStrength * 0.5;
      glass3Ref.current.position.y = mousePosition.y * parallaxStrength * 0.7;
      glass3Ref.current.position.z = -1 + Math.cos(time * 0.4) * 0.1;
    }
    
    if (glass4Ref.current) {
      glass4Ref.current.position.x = mousePosition.x * parallaxStrength * 0.3;
      glass4Ref.current.position.y = mousePosition.y * parallaxStrength * 0.4;
      glass4Ref.current.position.z = -1.5 + Math.sin(time * 0.6) * 0.05;
    }

    // Update material properties based on cognitive state
    const targetOpacity = getOpacityForState(cognitiveState);
    const targetTransmission = getTransmissionForState(cognitiveState);
    
    glassMaterial.opacity = THREE.MathUtils.lerp(glassMaterial.opacity, targetOpacity, delta * 2);
    glassMaterial.transmission = THREE.MathUtils.lerp(glassMaterial.transmission, targetTransmission, delta * 2);
    
    // Frustration glitch effect
    if (cognitiveState === 'FRUSTRATED') {
      glassMaterial.opacity += Math.sin(time * 20) * 0.1;
      glassMaterial.roughness = 0.1 + Math.random() * 0.2;
    } else {
      glassMaterial.roughness = THREE.MathUtils.lerp(glassMaterial.roughness, 0.1, delta * 5);
    }
  });

  const getOpacityForState = (state) => {
    switch (state) {
      case 'FLOWING': return 0.02; // Nearly invisible
      case 'STUCK': return 0.15;   // More visible
      case 'FRUSTRATED': return 0.2; // Most visible
      case 'IDLE': return 0.1;     // Moderate
      default: return 0.1;
    }
  };

  const getTransmissionForState = (state) => {
    switch (state) {
      case 'FLOWING': return 0.98; // Maximum transparency
      case 'STUCK': return 0.8;    // Reduced transparency
      case 'FRUSTRATED': return 0.7; // More opaque
      case 'IDLE': return 0.9;     // High transparency
      default: return 0.9;
    }
  };

  return (
    <group>
      {/* Glass Pane 1 - Frontmost */}
      <Plane
        ref={glass1Ref}
        args={[8, 6]}
        position={[0, 0, 0]}
        material={glassMaterial}
      />
      
      {/* Glass Pane 2 */}
      <Plane
        ref={glass2Ref}
        args={[7, 5]}
        position={[0.2, -0.1, -0.5]}
        material={glassMaterial}
      />
      
      {/* Glass Pane 3 */}
      <Plane
        ref={glass3Ref}
        args={[6, 4]}
        position={[-0.1, 0.2, -1]}
        material={glassMaterial}
      />
      
      {/* Glass Pane 4 - Backmost */}
      <Plane
        ref={glass4Ref}
        args={[5, 3]}
        position={[0.1, -0.2, -1.5]}
        material={glassMaterial}
      />
    </group>
  );
}