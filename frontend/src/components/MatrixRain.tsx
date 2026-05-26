import React, { useEffect, useRef } from 'react';

const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789⚽★▓░█═║┌┐└┘─│▶◄∞≈≡∑ΔΩ';
const FONT_SIZE = 11;

interface MatrixRainProps {
  opacity?: number;
}

export const MatrixRain: React.FC<MatrixRainProps> = ({ opacity = 0.04 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let drops: number[] = [];
    let animId: number;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      const cols = Math.floor(canvas.width / FONT_SIZE);
      drops = Array.from({ length: cols }, () => Math.random() * -100);
    };

    resize();
    window.addEventListener('resize', resize);

    const draw = () => {
      ctx.fillStyle = 'rgba(5, 7, 10, 0.06)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = `${FONT_SIZE}px monospace`;

      drops.forEach((y, i) => {
        const char = CHARS[Math.floor(Math.random() * CHARS.length)];
        const x = i * FONT_SIZE;
        // Bright leader, dim trail
        const isLeader = Math.random() > 0.92;
        ctx.fillStyle = isLeader ? '#00f2ff' : 'rgba(0,242,255,0.18)';
        ctx.fillText(char, x, y * FONT_SIZE);

        if (y * FONT_SIZE > canvas.height && Math.random() > 0.978) {
          drops[i] = 0;
        }
        drops[i] += 0.8;
      });

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
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        opacity,
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  );
};
