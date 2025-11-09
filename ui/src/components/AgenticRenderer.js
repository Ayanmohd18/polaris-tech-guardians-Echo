import React from 'react';
import './AgenticRenderer.css';

export default function AgenticRenderer() {
  return (
    <div className="agentic-renderer">
      <svg width="400" height="300" viewBox="0 0 400 300">
        {[...Array(20)].map((_, i) => (
          <g key={i}>
            <circle
              cx={50 + (i % 5) * 80}
              cy={50 + Math.floor(i / 5) * 60}
              r="3"
              className="neural-node"
              style={{ animationDelay: `${i * 0.1}s` }}
            />
            {i < 19 && (
              <line
                x1={50 + (i % 5) * 80}
                y1={50 + Math.floor(i / 5) * 60}
                x2={50 + ((i + 1) % 5) * 80}
                y2={50 + Math.floor((i + 1) / 5) * 60}
                className="neural-connection"
              />
            )}
          </g>
        ))}
        <circle className="data-packet" r="4">
          <animateMotion dur="3s" repeatCount="indefinite">
            <mpath href="#packet-path" />
          </animateMotion>
        </circle>
        <path id="packet-path" d="M 50,50 L 130,50 L 210,110 L 290,110 L 370,170" fill="none" />
      </svg>
    </div>
  );
}
