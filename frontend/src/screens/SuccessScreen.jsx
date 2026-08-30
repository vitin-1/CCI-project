/**
 * SuccessScreen — /success
 * Fluxo 2 / Etapa 9
 *
 * Tela de celebração exibida quando a busca encontrou fotos.
 * Dados recebidos via useLocation().state (passados pelo ProcessingScreen):
 *   total   — número total de fotos encontradas
 *   results — array de objetos Photo (para contar eventos únicos)
 *
 * Saídas:
 *   "Ver minhas fotos"    → / (ResultsScreen — resultados já no estado global)
 *   "Ver todos os eventos" → /events
 */

import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Confetti from '../components/Confetti';

export default function SuccessScreen() {
  const navigate = useNavigate();
  const { state: loc } = useLocation();
  const [confetti, setConfetti] = useState(true);

  const total = loc?.total || 0;
  const results = loc?.results || [];

  // Guard: sem dados de busca → volta para o início
  useEffect(() => {
    if (!loc?.total) navigate('/', { replace: true });
  }, []);

  // Conta eventos únicos presentes nos resultados para exibir na mensagem
  const eventCount = new Set(results.map((r) => r.event_id).filter(Boolean)).size;

  // Para o confetti após 4s (evita criar partículas infinitamente)
  useEffect(() => {
    const t = setTimeout(() => setConfetti(false), 4000);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="screen" style={{ justifyContent: 'center', alignItems: 'center', gap: 28, textAlign: 'center' }}>
      <Confetti active={confetti} />

      {/* Checkmark animado */}
      <div
        className="anim-zoom-in"
        style={{
          width: 96, height: 96,
          background: 'var(--accent-dim)',
          border: '2px solid var(--accent)',
          borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 0 40px rgba(74,222,128,0.3)',
        }}
      >
        <svg width="44" height="44" viewBox="0 0 24 24" fill="none">
          <polyline
            points="4,12 9,17 20,6"
            stroke="var(--accent)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray="60"
            strokeDashoffset="0"
            style={{ animation: 'checkDraw 0.6s 0.3s ease forwards' }}
          />
        </svg>
      </div>

      <div className="anim-fade-in-up delay-2">
        <h1 style={{ marginBottom: 12 }}>Encontramos você!</h1>
        <p style={{ fontSize: 16, color: 'var(--text)' }}>
          Você apareceu em <strong style={{ color: 'var(--accent)' }}>{total} foto{total !== 1 ? 's' : ''}</strong>
          {eventCount > 0 && (
            <> em <strong style={{ color: 'var(--accent)' }}>{eventCount} evento{eventCount !== 1 ? 's' : ''}</strong></>
          )}.
        </p>
      </div>

      <div className="anim-fade-in-up delay-3" style={{ display: 'flex', flexDirection: 'column', gap: 12, width: '100%' }}>
        <button className="btn btn-primary" onClick={() => navigate('/', { replace: true })}>
          Ver minhas fotos
        </button>
        <button className="btn btn-ghost" onClick={() => navigate('/events')}>
          Ver todos os eventos
        </button>
      </div>
    </div>
  );
}
