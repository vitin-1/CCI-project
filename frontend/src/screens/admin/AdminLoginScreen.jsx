/**
 * AdminLoginScreen — /admin
 * Fluxo 5 / Etapa 15
 *
 * Autenticação do painel administrativo via token estático.
 * Valida o token chamando GET /admin/queue — se retornar 403, token inválido.
 *
 * Armazena em sessionStorage (NUNCA localStorage) para que o token
 * não persista após fechar o browser.
 *
 * Saída: /admin/queue após validação bem-sucedida
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/client';

export default function AdminLoginScreen() {
  const navigate = useNavigate();
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleLogin(e) {
    e.preventDefault();
    if (!token.trim()) return;
    setLoading(true);
    setError('');
    try {
      // Valida o token fazendo uma chamada real à fila — evita endpoint dedicado de auth
      await api.admin.getQueue(token.trim());
      sessionStorage.setItem('cciAdminToken', token.trim());
      navigate('/admin/queue', { replace: true });
    } catch (err) {
      if (err.status === 403) setError('Token inválido. Verifique e tente novamente.');
      else setError(err.message || 'Erro ao autenticar.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="screen" style={{ justifyContent: 'center', gap: 28, paddingTop: 40 }}>
      <div className="anim-fade-in-up" style={{ textAlign: 'center' }}>
        <img
          src="/logo.jpg"
          alt="CCI Aliança"
          style={{ width: 80, height: 80, borderRadius: '50%', objectFit: 'cover', marginBottom: 20 }}
        />
        <h2 style={{ marginBottom: 6 }}>Painel Admin</h2>
        <p>CCI Aliança — Fila de Revisão</p>
      </div>

      <form className="anim-fade-in-up delay-1" onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div>
          <label className="input-label" htmlFor="admin-token">Token de administrador</label>
          <input
            id="admin-token"
            className="input"
            type="password"
            placeholder="••••••••••"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>
        {error && <div className="error-msg">{error}</div>}
        <button type="submit" className="btn btn-primary" disabled={!token.trim() || loading}>
          {loading ? <span className="spinner" /> : 'Entrar'}
        </button>
      </form>
    </div>
  );
}
