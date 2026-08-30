import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

export default function SplashScreen() {
  const navigate = useNavigate();
  const { state } = useApp();

  useEffect(() => {
    // Usuários logados não precisam esperar a animação completa
    const delay = state.memberId ? 800 : 2200;
    const t = setTimeout(() => {
      navigate(state.memberId ? '/' : '/welcome', { replace: true });
    }, delay);
    return () => clearTimeout(t);
  }, [state.memberId, navigate]);

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg)',
      gap: 24,
    }}>
      <img
        src="/logo.jpg"
        alt="CCI Aliança"
        className="anim-zoom-in"
        style={{ width: 160, height: 160, borderRadius: '50%', objectFit: 'cover' }}
      />

      <div className="anim-fade-in-up delay-3" style={{ textAlign: 'center' }}>
        <h1 style={{ color: 'var(--accent)', fontSize: 22, marginBottom: 4 }}>CCI ALIANÇA</h1>
        <p style={{ fontSize: 13 }}>Encontre seus momentos</p>
      </div>

      {/* Indicador de carregamento */}
      <div className="anim-fade-in-up delay-5" style={{ display: 'flex', gap: 8 }}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              width: 7, height: 7,
              borderRadius: '50%',
              background: 'var(--accent)',
              animation: `pulse 1.4s ease-in-out ${i * 0.28}s infinite`,
            }}
          />
        ))}
      </div>
    </div>
  );
}
