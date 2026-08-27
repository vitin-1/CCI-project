/**
 * CaptureScreen — /capture
 * Fluxo 2 / Etapa 7
 *
 * Acessa a câmera frontal via getUserMedia e captura uma selfie quadrada.
 * Saída: navega para /processing com state.selfie = Blob (JPEG, qualidade 0.92)
 *
 * Pontos de atenção para manutenção:
 *   - streamRef: a referência à MediaStream deve ser parada no cleanup do useEffect
 *     (ao navegar ou desmontar) para liberar o indicador de câmera no dispositivo
 *   - Canvas crop: extrai um quadrado centralizado do frame para evitar distorção
 *   - Estado "denied": câmera negada pelo usuário → fallback para galeria
 */

import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function CaptureScreen() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);  // guarda a MediaStream para poder pará-la no cleanup
  const [ready, setReady] = useState(false);
  const [denied, setDenied] = useState(false);
  const [flash, setFlash] = useState(false);

  useEffect(() => {
    startCamera();
    // Cleanup: para todos os tracks ao sair da tela (libera câmera no OS)
    return () => streamRef.current?.getTracks().forEach((t) => t.stop());
  }, []);

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 720 }, height: { ideal: 720 } },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => setReady(true);
      }
    } catch {
      setDenied(true);
    }
  }

  function capture() {
    if (!ready) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Crop quadrado centralizado — mantém proporção sem distorção
    const size = Math.min(video.videoWidth, video.videoHeight);
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    const offsetX = (video.videoWidth - size) / 2;
    const offsetY = (video.videoHeight - size) / 2;
    ctx.drawImage(video, offsetX, offsetY, size, size, 0, 0, size, size);

    setFlash(true);
    setTimeout(() => setFlash(false), 300);

    canvas.toBlob(
      (blob) => {
        streamRef.current?.getTracks().forEach((t) => t.stop());
        navigate('/processing', { state: { selfie: blob } });
      },
      'image/jpeg',
      0.92,
    );
  }

  // ─── Estado: permissão negada ─────────────────────────────────────────────

  if (denied) {
    return (
      <div className="screen" style={{ justifyContent: 'center', gap: 20, textAlign: 'center' }}>
        <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
          <line x1="1" y1="1" x2="23" y2="23" />
        </svg>
        <h2>Câmera bloqueada</h2>
        <p>Permita o acesso à câmera nas configurações do seu dispositivo e tente novamente.</p>
        <button className="btn btn-outline" onClick={() => navigate('/choose')}>Enviar da galeria</button>
        <button className="btn btn-ghost" onClick={() => navigate(-1)}>Voltar</button>
      </div>
    );
  }

  // ─── Estado normal: câmera ativa ──────────────────────────────────────────

  return (
    <div className="screen-full" style={{ position: 'relative', background: '#000' }}>
      {/* Flash visual ao capturar */}
      {flash && (
        <div style={{
          position: 'absolute', inset: 0, background: '#fff',
          opacity: 0.7, zIndex: 10, pointerEvents: 'none',
          animation: 'fadeIn 0.05s',
        }} />
      )}

      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />
      {/* Canvas oculto — usado apenas para capturar o frame */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Overlay: guia de rosto + botão de captura */}
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {/* Botão fechar */}
        <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', padding: '16px 20px' }}>
          <button
            onClick={() => { streamRef.current?.getTracks().forEach((t) => t.stop()); navigate(-1); }}
            style={{ background: 'rgba(0,0,0,0.5)', border: 'none', borderRadius: '50%', width: 40, height: 40, color: '#fff', fontSize: 20, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            aria-label="Fechar"
          >
            ×
          </button>
        </div>

        {/* Guia circular de rosto */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
          <p style={{ color: '#fff', fontSize: 14, fontWeight: 600, textShadow: '0 1px 4px rgba(0,0,0,0.8)', marginBottom: 8 }}>
            Centralize seu rosto
          </p>
          <div style={{
            width: 220, height: 220,
            border: `3px solid ${ready ? 'var(--accent)' : 'rgba(255,255,255,0.4)'}`,
            borderRadius: '50%',
            position: 'relative',
            boxShadow: ready ? '0 0 0 2px rgba(74,222,128,0.3), 0 0 30px rgba(74,222,128,0.2)' : 'none',
            transition: 'border-color 0.5s, box-shadow 0.5s',
          }}>
            {ready && (
              <div style={{
                position: 'absolute', left: '10%', width: '80%', height: 2,
                background: 'linear-gradient(90deg, transparent, var(--accent), transparent)',
                top: '0%', animation: 'scanLine 2s ease-in-out infinite',
              }} />
            )}
            {/* Marcadores de canto */}
            {['top-left','top-right','bottom-left','bottom-right'].map((pos) => {
              const [v, h] = pos.split('-');
              return (
                <div key={pos} style={{
                  position: 'absolute',
                  [v]: -3, [h]: -3,
                  width: 20, height: 20,
                  border: `3px solid var(--accent)`,
                  [`border${v.charAt(0).toUpperCase()+v.slice(1)}${h.charAt(0).toUpperCase()+h.slice(1)}Radius`]: 4,
                  borderBottom: v === 'top' ? 'none' : undefined,
                  borderTop: v === 'bottom' ? 'none' : undefined,
                  borderRight: h === 'left' ? 'none' : undefined,
                  borderLeft: h === 'right' ? 'none' : undefined,
                }} />
              );
            })}
          </div>
        </div>

        {/* Botão de captura */}
        <div style={{ paddingBottom: 48, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
          <button
            onClick={capture}
            disabled={!ready}
            aria-label="Tirar foto"
            style={{
              width: 72, height: 72, borderRadius: '50%',
              background: ready ? '#fff' : 'rgba(255,255,255,0.3)',
              border: '4px solid rgba(255,255,255,0.6)',
              cursor: ready ? 'pointer' : 'not-allowed',
              transition: 'transform 0.15s',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
            onMouseDown={(e) => { e.currentTarget.style.transform = 'scale(0.93)'; }}
            onMouseUp={(e) => { e.currentTarget.style.transform = 'scale(1)'; }}
          >
            <div style={{ width: 56, height: 56, borderRadius: '50%', background: ready ? '#fff' : 'rgba(255,255,255,0.3)' }} />
          </button>
          {!ready && <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13 }}>Iniciando câmera...</p>}
        </div>
      </div>
    </div>
  );
}
