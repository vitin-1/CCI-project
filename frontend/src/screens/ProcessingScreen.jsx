/**
 * ProcessingScreen — /processing
 * Fluxo 2 / Etapa 8
 *
 * Executa a busca facial e exibe feedback visual enquanto aguarda.
 * Recebe: useLocation().state.selfie (Blob da câmera ou File da galeria)
 *
 * Saídas:
 *   Fotos encontradas   → /success  com { total, results }
 *   Sem fotos           → /         com { empty: true }
 *   CONSENT_REQUIRED    → /consent  (backend rejeitou — consent expirou)
 *   NO_FACE_DETECTED    → erro inline com mensagem específica
 *   Outros erros        → erro inline com "Tentar novamente" → /choose
 *
 * Atenção — StrictMode guard (ranRef):
 *   React 18 no modo desenvolvimento monta → desmonta → remonta componentes.
 *   Sem o guard, o useEffect dispararia duas chamadas POST /search.
 *   ranRef.current evita a segunda chamada sem interferir na produção.
 */

import { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '../api/client';
import { useApp } from '../context/AppContext';

// Mensagens de status exibidas em ciclo enquanto a API processa
const STAGES = [
  'Detectando seu rosto...',
  'Buscando nos eventos...',
  'Analisando correspondências...',
  'Quase lá...',
];

export default function ProcessingScreen() {
  const navigate = useNavigate();
  const { state: loc } = useLocation();
  const { state, dispatch } = useApp();
  const [stageIdx, setStageIdx] = useState(0);
  const [error, setError] = useState('');
  const ranRef = useRef(false);  // guard StrictMode — ver comentário no topo

  useEffect(() => {
    if (ranRef.current) return;
    ranRef.current = true;

    // Redireciona se chegou aqui sem selfie ou sem sessão
    if (!loc?.selfie || !state.memberId) {
      navigate('/choose', { replace: true });
      return;
    }

    // Cicla pelas mensagens de status a cada 2,2s enquanto aguarda a resposta
    const interval = setInterval(() => {
      setStageIdx((i) => Math.min(i + 1, STAGES.length - 1));
    }, 2200);

    api
      .search(state.memberId, loc.selfie)
      .then((data) => {
        clearInterval(interval);
        dispatch({ type: 'SET_RESULTS', results: data.results || [] });
        if (data.total > 0) {
          // Merge das fotos novas no histórico persistido
          dispatch({ type: 'ADD_MY_PHOTOS', photos: data.results });
          navigate('/success', { replace: true, state: { total: data.total, results: data.results } });
        } else {
          navigate('/', { replace: true, state: { empty: true } });
        }
      })
      .catch((err) => {
        clearInterval(interval);
        if (err.code === 'NO_FACE_DETECTED') {
          setError('Nenhum rosto detectado na foto. Tente uma foto com o rosto bem visível.');
        } else if (err.code === 'CONSENT_REQUIRED') {
          navigate('/consent', { replace: true });
        } else {
          setError(err.message || 'Erro ao buscar fotos. Tente novamente.');
        }
      });

    return () => clearInterval(interval);
  }, []);

  // ─── Estado de erro ───────────────────────────────────────────────────────

  if (error) {
    return (
      <div className="screen" style={{ justifyContent: 'center', gap: 20, textAlign: 'center' }}>
        <div style={{ fontSize: 56 }}>😕</div>
        <h2>Algo deu errado</h2>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => navigate('/choose')}>Tentar novamente</button>
      </div>
    );
  }

  // ─── Estado de carregamento ───────────────────────────────────────────────

  return (
    <div className="screen" style={{ justifyContent: 'center', alignItems: 'center', gap: 32, textAlign: 'center' }}>
      {/* Logo com anéis de ripple enquanto processa */}
      <div style={{ position: 'relative', width: 120, height: 120 }}>
        <div style={{ position: 'absolute', inset: -12, border: '2px solid var(--accent)', borderRadius: '50%', opacity: 0.4, animation: 'ripple 1.8s ease-out infinite' }} />
        <div style={{ position: 'absolute', inset: -24, border: '1.5px solid var(--accent)', borderRadius: '50%', opacity: 0.2, animation: 'ripple 1.8s 0.6s ease-out infinite' }} />
        <img
          src="/logo.jpg"
          alt="CCI"
          style={{ width: 120, height: 120, borderRadius: '50%', objectFit: 'cover', animation: 'pulse 2s ease-in-out infinite' }}
        />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
        <h2 style={{ fontSize: 20 }}>Procurando por você...</h2>
        {/* key={stageIdx} força re-render e reinicia a transição de opacidade */}
        <p style={{ minHeight: 24, transition: 'opacity 0.4s' }} key={stageIdx}>
          {STAGES[stageIdx]}
        </p>
        <div className="spinner spinner-lg" style={{ marginTop: 8 }} />
      </div>
    </div>
  );
}
