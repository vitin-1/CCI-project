/**
 * SplashScreen — /splash
 * Fluxo 1 / Etapa 1
 *
 * Primeira tela carregada. Após 2,2s redireciona:
 *   - com sessão  → / (ResultsScreen)
 *   - sem sessão  → /welcome
 *
 * Também é o destino da rota wildcard (*) — qualquer URL inválida cai aqui.
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

export default function SplashScreen() {
  const navigate = useNavigate();
  const { state } = useApp();

  useEffect(() => {
    const t = setTimeout(() => {
      if (state.memberId) {
        navigate('/', { replace: true });
      } else {
        navigate('/welcome', { replace: true });
      }
    }, 2200);
    return () => clearTimeout(t);
  }, []);

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
      <div className="anim-fade-in delay-3" style={{ textAlign: 'center' }}>
        <h1 style={{ color: 'var(--accent)', fontSize: 22, marginBottom: 4 }}>CCI ALIANÇA</h1>
        <p style={{ fontSize: 13 }}>Encontre seus momentos</p>
      </div>
    </div>
  );
}
