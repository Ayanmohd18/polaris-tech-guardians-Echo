import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';

export default function SentientGlass({ blur, mode }) {
  const pane1 = useRef();
  const pane2 = useRef();
  const pane3 = useRef();

  useFrame(({ mouse }) => {
    if (pane1.current) pane1.current.position.x = mouse.x * 0.1;
    if (pane2.current) pane2.current.position.x = mouse.x * 0.15;
    if (pane3.current) pane3.current.position.x = mouse.x * 0.2;
  });

  const glassOpacity = blur === 0 ? 0.1 : 0.3;
  const glassColor = mode === 'ambient' ? '#1a1a2e' : '#f0f0f5';

  return (
    <group>
      <mesh ref={pane1} position={[0, 0, 0]}>
        <planeGeometry args={[8, 6]} />
        <meshPhysicalMaterial
          color={glassColor}
          transparent
          opacity={glassOpacity}
          roughness={0.1}
          metalness={0.1}
          transmission={0.9}
          thickness={0.5}
        />
      </mesh>

      <mesh ref={pane2} position={[0, 0, -0.5]}>
        <planeGeometry args={[8, 6]} />
        <meshPhysicalMaterial
          color={glassColor}
          transparent
          opacity={glassOpacity * 0.8}
          roughness={0.1}
          metalness={0.1}
          transmission={0.9}
          thickness={0.5}
        />
      </mesh>

      <mesh ref={pane3} position={[0, 0, -1]}>
        <planeGeometry args={[8, 6]} />
        <meshPhysicalMaterial
          color={glassColor}
          transparent
          opacity={glassOpacity * 0.6}
          roughness={0.1}
          metalness={0.1}
          transmission={0.9}
          thickness={0.5}
        />
      </mesh>
    </group>
  );
}
