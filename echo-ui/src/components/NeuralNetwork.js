import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export function NeuralNetwork() {
  const networkRef = useRef();
  const linesRef = useRef();

  // Generate neural network nodes and connections
  const networkData = useMemo(() => {
    const nodeCount = 20;
    const nodes = [];
    const connections = [];
    
    // Create nodes in 3D space
    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        position: new THREE.Vector3(
          (Math.random() - 0.5) * 6,
          (Math.random() - 0.5) * 4,
          (Math.random() - 0.5) * 2
        ),
        phase: Math.random() * Math.PI * 2,
        speed: 0.5 + Math.random() * 1.5
      });
    }
    
    // Create connections between nearby nodes
    for (let i = 0; i < nodeCount; i++) {
      for (let j = i + 1; j < nodeCount; j++) {
        const distance = nodes[i].position.distanceTo(nodes[j].position);
        if (distance < 2.5 && Math.random() > 0.6) {
          connections.push({
            from: i,
            to: j,
            strength: Math.random(),
            phase: Math.random() * Math.PI * 2
          });
        }
      }
    }
    
    return { nodes, connections };
  }, []);

  // Create line geometry for connections
  const lineGeometry = useMemo(() => {
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(networkData.connections.length * 6); // 2 points per line, 3 coords per point
    const colors = new Float32Array(networkData.connections.length * 6); // 2 colors per line, 3 components per color
    
    networkData.connections.forEach((connection, i) => {
      const fromNode = networkData.nodes[connection.from];
      const toNode = networkData.nodes[connection.to];
      
      // Line positions
      positions[i * 6] = fromNode.position.x;
      positions[i * 6 + 1] = fromNode.position.y;
      positions[i * 6 + 2] = fromNode.position.z;
      positions[i * 6 + 3] = toNode.position.x;
      positions[i * 6 + 4] = toNode.position.y;
      positions[i * 6 + 5] = toNode.position.z;
      
      // Line colors (Ndot57 style - white/blue)
      const color = new THREE.Color().setHSL(0.6, 0.8, 0.8);
      colors[i * 6] = color.r;
      colors[i * 6 + 1] = color.g;
      colors[i * 6 + 2] = color.b;
      colors[i * 6 + 3] = color.r;
      colors[i * 6 + 4] = color.g;
      colors[i * 6 + 5] = color.b;
    });
    
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    
    return geometry;
  }, [networkData]);

  useFrame((state, delta) => {
    const time = state.clock.getElapsedTime();
    
    if (networkRef.current) {
      // Gentle rotation of entire network
      networkRef.current.rotation.y += delta * 0.1;
      networkRef.current.rotation.x = Math.sin(time * 0.2) * 0.1;
    }
    
    // Animate connection lines
    if (linesRef.current) {
      const positions = linesRef.current.geometry.attributes.position.array;
      const colors = linesRef.current.geometry.attributes.color.array;
      
      networkData.connections.forEach((connection, i) => {
        // Pulsing effect on connections
        const pulse = Math.sin(time * connection.speed + connection.phase) * 0.5 + 0.5;
        const opacity = 0.3 + pulse * 0.7;
        
        // Update colors with pulsing opacity
        const baseColor = new THREE.Color().setHSL(0.6, 0.8, 0.5 + pulse * 0.3);
        colors[i * 6] = baseColor.r * opacity;
        colors[i * 6 + 1] = baseColor.g * opacity;
        colors[i * 6 + 2] = baseColor.b * opacity;
        colors[i * 6 + 3] = baseColor.r * opacity;
        colors[i * 6 + 4] = baseColor.g * opacity;
        colors[i * 6 + 5] = baseColor.b * opacity;
      });
      
      linesRef.current.geometry.attributes.color.needsUpdate = true;
    }
  });

  return (
    <group ref={networkRef} position={[0, 0, -2]}>
      {/* Neural Network Nodes */}
      {networkData.nodes.map((node, index) => (
        <mesh key={index} position={node.position}>
          <sphereGeometry args={[0.05, 8, 8]} />
          <meshBasicMaterial
            color="#ffffff"
            transparent={true}
            opacity={0.8}
          />
        </mesh>
      ))}
      
      {/* Neural Network Connections */}
      <lineSegments ref={linesRef} geometry={lineGeometry}>
        <lineBasicMaterial
          vertexColors={true}
          transparent={true}
          opacity={0.6}
          linewidth={2}
        />
      </lineSegments>
      
      {/* Data Packets flowing through connections */}
      {networkData.connections.slice(0, 5).map((connection, index) => (
        <DataPacket
          key={index}
          fromNode={networkData.nodes[connection.from]}
          toNode={networkData.nodes[connection.to]}
          speed={connection.strength * 2}
          delay={index * 0.5}
        />
      ))}
    </group>
  );
}

// Data packet component that flows along connections
function DataPacket({ fromNode, toNode, speed, delay }) {
  const packetRef = useRef();
  
  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    const progress = ((time * speed + delay) % 2) / 2; // 0 to 1 and repeat
    
    if (packetRef.current) {
      // Interpolate position along the connection
      const currentPos = fromNode.position.clone().lerp(toNode.position, progress);
      packetRef.current.position.copy(currentPos);
      
      // Fade in/out effect
      const opacity = Math.sin(progress * Math.PI) * 0.8;
      packetRef.current.material.opacity = opacity;
    }
  });
  
  return (
    <mesh ref={packetRef}>
      <sphereGeometry args={[0.02, 6, 6]} />
      <meshBasicMaterial
        color="#00ffff"
        transparent={true}
        opacity={0.8}
      />
    </mesh>
  );
}