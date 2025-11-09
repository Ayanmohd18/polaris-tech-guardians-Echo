import React, { useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';

export default function PhotonicShift({ mode }) {
  const sunRef = useRef();
  const progress = useRef(mode === 'focus' ? 1 : 0);

  useEffect(() => {
    progress.current = mode === 'focus' ? 1 : 0;
  }, [mode]);

  useFrame((state, delta) => {
    const target = mode === 'focus' ? 1 : 0;
    progress.current += (target - progress.current) * delta * 2;

    if (sunRef.current) {
      sunRef.current.position.x = -5 + progress.current * 10;
      sunRef.current.position.y = -2 + progress.current * 4;
      sunRef.current.intensity = progress.current * 5;
    }
  });

  return (
    <directionalLight
      ref={sunRef}
      color={mode === 'focus' ? '#ffd700' : '#4a90e2'}
      intensity={0}
      position={[-5, -2, 2]}
      castShadow
    />
  );
}
