import React, { useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
// Using Three.js lights directly
import * as THREE from 'three';

export function PhotonicShift({ ambientMode }) {
  const sunLightRef = useRef();
  const ambientLightRef = useRef();
  const transitionProgress = useRef(ambientMode ? 0 : 1);

  useFrame((state, delta) => {
    const time = state.clock.getElapsedTime();
    
    // Smooth transition between modes
    const targetProgress = ambientMode ? 0 : 1;
    transitionProgress.current = THREE.MathUtils.lerp(
      transitionProgress.current, 
      targetProgress, 
      delta * 2
    );
    
    if (sunLightRef.current) {
      // Sunrise/Sunset animation
      const progress = transitionProgress.current;
      
      // Sun position (rises from side)
      const sunAngle = (progress - 0.5) * Math.PI;
      sunLightRef.current.position.set(
        Math.cos(sunAngle) * 10,
        Math.sin(sunAngle) * 5 + 2,
        5
      );
      
      // Sun intensity and color
      const sunIntensity = Math.max(0, Math.sin(sunAngle)) * 2;
      sunLightRef.current.intensity = sunIntensity;
      
      // Color temperature shift
      const warmth = progress;
      const sunColor = new THREE.Color().setHSL(
        0.1 * (1 - warmth), // Hue: blue to warm
        0.2 + warmth * 0.3, // Saturation
        0.8 + warmth * 0.2  // Lightness
      );
      sunLightRef.current.color = sunColor;
      
      // Shadow properties for caustic effects
      sunLightRef.current.castShadow = progress > 0.1;
      if (sunLightRef.current.shadow) {
        sunLightRef.current.shadow.mapSize.width = 2048;
        sunLightRef.current.shadow.mapSize.height = 2048;
        sunLightRef.current.shadow.camera.near = 0.5;
        sunLightRef.current.shadow.camera.far = 50;
        sunLightRef.current.shadow.camera.left = -10;
        sunLightRef.current.shadow.camera.right = 10;
        sunLightRef.current.shadow.camera.top = 10;
        sunLightRef.current.shadow.camera.bottom = -10;
      }
    }
    
    if (ambientLightRef.current) {
      // Ambient light adjustment
      const progress = transitionProgress.current;
      
      // Ambient Mode: Low ambient, high contrast
      // Focus Mode: High ambient, soft shadows
      ambientLightRef.current.intensity = ambientMode ? 0.2 : 0.8;
      
      // Color temperature
      const ambientColor = new THREE.Color().setHSL(
        0.6 * (1 - progress), // Blue to neutral
        0.1 + progress * 0.2, // Low saturation
        0.3 + progress * 0.4  // Brightness
      );
      ambientLightRef.current.color = ambientColor;
    }
  });

  return (
    <group>
      {/* Directional Light (Sun) */}
      <directionalLight
        ref={sunLightRef}
        position={[-10, 2, 5]}
        intensity={0}
        color="#ffffff"
        castShadow
      />
      
      {/* Ambient Light */}
      <ambientLight
        ref={ambientLightRef}
        intensity={ambientMode ? 0.2 : 0.8}
        color="#ffffff"
      />
      
      {/* Additional atmospheric effects could go here */}
      {/* Fog, volumetric lighting, etc. */}
    </group>
  );
}