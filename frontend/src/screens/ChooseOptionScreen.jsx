/**
 * ChooseOptionScreen — /choose
 * Fluxo 2 / Etapa 6
 *
 * Ponto de entrada do fluxo de busca. Duas opções:
 *   Câmera   → /capture (CaptureScreen)
 *   Galeria  → file input oculto → /processing com state.selfie = File
 *
 * O objeto File é estruturalmente clonável e sobrevive ao navigate() do React Router.
 * Dentro do FlowLayout (sem BottomNav) para experiência em tela cheia.
 */

import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';

export default function ChooseOptionScreen() {
  const navigate = useNavigate();
  const fileRef = useRef(null);

  function handleFileSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    // Passa o File via navigation state — chega em ProcessingScreen como loc.selfie
    navigate('/processing', { state: { selfie: file } });
  }

  return (
    <div className="screen" style={{ justifyContent: 'center', gap: 32, paddingTop: 60 }}>
      <div className="anim-fade-in-up" style={{ textAlign: 'center' }}>
        <h2 style={{ marginBottom: 8 }}>Como você quer{'\n'}encontrar suas fotos?</h2>
        <p>Escolha uma das opções abaixo</p>
      </div>

      <div className="anim-fade-in-up delay-1" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {/* Opção 1: câmera */}
        <button
          className="card"
          onClick={() => navigate('/capture')}
          style={{
            display: 'flex', alignItems: 'center', gap: 16,
            cursor: 'pointer', border: 'none', width: '100%', textAlign: 'left',
            transition: 'transform 0.15s, border-color 0.15s',
            animation: 'fadeInScale 0.4s 0.1s ease forwards', opacity: 0,
          }}
        >
          <div style={{
            width: 60, height: 60, background: 'var(--accent-dim)', borderRadius: 16,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
          </div>
          <div>
            <h3 style={{ marginBottom: 4 }}>Tirar uma Foto</h3>
            <p style={{ fontSize: 13 }}>Use a câmera para tirar uma selfie agora.</p>
          </div>
        </button>

        {/* Opção 2: galeria — input oculto acionado pelo botão */}
        <button
          className="card"
          onClick={() => fileRef.current?.click()}
          style={{
            display: 'flex', alignItems: 'center', gap: 16,
            cursor: 'pointer', border: 'none', width: '100%', textAlign: 'left',
            animation: 'fadeInScale 0.4s 0.2s ease forwards', opacity: 0,
          }}
        >
          <div style={{
            width: 60, height: 60, background: 'var(--accent-dim)', borderRadius: 16,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
          </div>
          <div>
            <h3 style={{ marginBottom: 4 }}>Enviar da Galeria</h3>
            <p style={{ fontSize: 13 }}>Escolha uma foto da sua galeria.</p>
          </div>
        </button>
      </div>

      {/* Input oculto — accept="image/*" abre galeria no mobile */}
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleFileSelect}
      />

      <button
        className="btn btn-ghost anim-fade-in-up delay-3"
        onClick={() => navigate(-1)}
        style={{ color: 'var(--text-muted)' }}
      >
        Voltar
      </button>
    </div>
  );
}
