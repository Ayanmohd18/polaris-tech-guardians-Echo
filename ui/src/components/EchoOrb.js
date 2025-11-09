import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere } from '@react-three/drei';

export default function EchoOrb({ state, thinking }) {
  const orbRef = useRef();
  const lightRef = useRef();

  useFrame(({ clock }) => {
    if (orbRef.current) {
      const pulse = state === 'STUCK' ? Math.sin(clock.elapsedTime * 2) * 0.1 + 1 : 1;
      orbRef.current.scale.setScalar(pulse);
    }
    if (lightRef.current && thinking) {
      lightRef.current.intensity = Math.sin(clock.elapsedTime * 3) * 2 + 3;
    }
  });

  const orbColor = state === 'STUCK' ? '#4a90e2' : state === 'FRUSTRATED' ? '#e24a4a' : '#64c8ff';

  return (
    <group position={[3, 2, 1]}>
      <Sphere ref={orbRef} args={[0.3, 32, 32]}>
        <meshStandardMaterial
          color={orbColor}
          emissive={orbColor}
          emissiveIntensity={thinking ? 2 : 1}
          roughness={0.2}
          metalness={0.8}
        />
      </Sphere>
      <pointLight ref={lightRef} color={orbColor} intensity={3} distance={10} />
    </group>
  );
}
