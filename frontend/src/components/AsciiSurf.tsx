import React, { useEffect, useRef } from 'react';

/**
 * AsciiSurf — A looping ASCII wave animation.
 *
 * Renders a seamless, undulating 3D wave pattern using ASCII characters.
 * Placed at the bottom of the screen to give a sophisticated tech aesthetic.
 */

interface AsciiSurfProps {
  opacity?: number;
}

export const AsciiSurf: React.FC<AsciiSurfProps> = ({ opacity = 0.4 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let time = 0;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    // Characters sorted by visual density (light to dark)
    const CHARS = [' ', ' ', '.', ',', ':', '/', '\\', 'X', 'O', '0'];
    
    const CHAR_W = 12;
    const CHAR_H = 14;

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.font = `14px monospace`;
      
      const cols = Math.ceil(canvas.width / CHAR_W);
      // Start the wave lower down
      const startY = canvas.height * 0.65; 
      const rows = Math.ceil((canvas.height - startY) / CHAR_H) + 5;

      for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
          // Generate a wave using multiple sine functions
          const nx = x * 0.04;
          const ny = y * 0.15;
          const nt = time * 0.03;
          
          let noise = Math.sin(nx + nt) * 0.6 + 
                      Math.sin(ny - nt * 0.8) * 0.4 + 
                      Math.sin(nx * 0.3 + ny * 0.5 + nt * 1.5) * 0.3;
          
          // Add perspective
          noise *= (1 + y * 0.15); 
          
          let charIdx = Math.floor(((noise + 1.2) / 2.4) * CHARS.length);
          charIdx = Math.max(0, Math.min(CHARS.length - 1, charIdx));
          
          const char = CHARS[charIdx];
          
          if (char !== ' ') {
            // Brighten it up to match the reference style
            const alpha = Math.min(1, Math.max(0.2, (y / rows) * 2));
            ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.6})`;
            
            const yOffset = noise * 12;
            ctx.fillText(char, x * CHAR_W, startY + y * CHAR_H + yOffset);
          }
        }
      }

      time += 0.5;
      animId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100%',
        opacity,
        pointerEvents: 'none',
        zIndex: -1, // Keep it behind everything
      }}
    />
  );
};
