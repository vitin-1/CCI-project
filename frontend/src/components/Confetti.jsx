/**
 * Confetti — animação de celebração
 * Usada na SuccessScreen. Ativa enquanto prop `active` for true.
 * Gera 90 partículas via DOM imperativo (melhor performance que 90 elementos React).
 * Para automaticamente após 4s (controlado pelo pai via setTimeout).
 */

import { useEffect, useRef } from 'react';

const COLORS = ['#4ade80', '#22c55e', '#fbbf24', '#f472b6', '#60a5fa', '#a78bfa', '#fb923c'];

export default function Confetti({ active }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!active || !ref.current) return;
    const container = ref.current;
    container.innerHTML = '';

    for (let i = 0; i < 90; i++) {
      const el = document.createElement('div');
      const color = COLORS[Math.floor(Math.random() * COLORS.length)];
      const size = Math.random() * 10 + 5;
      const left = Math.random() * 100;
      const delay = Math.random() * 1.5;
      const dur = Math.random() * 2 + 2;
      const isRect = Math.random() > 0.5;

      el.style.cssText = `
        position: absolute;
        left: ${left}%;
        top: -20px;
        width: ${size}px;
        height: ${isRect ? size * 0.5 : size}px;
        background: ${color};
        border-radius: ${isRect ? '2px' : '50%'};
        animation: confettiFall ${dur}s ${delay}s ease-in forwards;
        pointer-events: none;
      `;
      container.appendChild(el);
    }
  }, [active]);

  if (!active) return null;
  return (
    <div
      ref={ref}
      style={{
        position: 'fixed',
        inset: 0,
        pointerEvents: 'none',
        overflow: 'hidden',
        zIndex: 999,
      }}
    />
  );
}
