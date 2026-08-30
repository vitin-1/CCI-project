/**
 * RegisterScreen — /register
 * Fluxo 1 / Etapa 4
 *
 * Cadastro de novo membro com nome e WhatsApp.
 * Guard em App.jsx: se já autenticado → /.
 *
 * API: POST /register { full_name, whatsapp }
 * Sucesso: dispatch SET_MEMBER → /consent
 * Erro 409 WHATSAPP_ALREADY_REGISTERED: mensagem inline (sem toast)
 *
 * Validação local:
 *   - nome: mínimo 2 caracteres
 *   - whatsapp: mínimo 12 dígitos brutos (+55 + DDD + número)
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useApp } from '../context/AppContext';

// Formata digitação em tempo real: +55 (11) 99999-9999
function formatWhatsApp(raw) {
  const digits = raw.replace(/\D/g, '');
  if (!digits) return '';
  if (digits.length <= 2) return `+${digits}`;
  if (digits.length <= 4) return `+${digits.slice(0,2)} (${digits.slice(2)}`;
  if (digits.length <= 9) return `+${digits.slice(0,2)} (${digits.slice(2,4)}) ${digits.slice(4)}`;
  return `+${digits.slice(0,2)} (${digits.slice(2,4)}) ${digits.slice(4,9)}-${digits.slice(9,13)}`;
}

export default function RegisterScreen() {
  const navigate = useNavigate();
  const { dispatch } = useApp();
  const [name, setName] = useState('');
  const [whatsapp, setWhatsapp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const rawDigits = whatsapp.replace(/\D/g, '');
  const validPhone = rawDigits.length >= 12;
  const valid = name.trim().length >= 2 && validPhone;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!valid) return;
    setLoading(true);
    setError('');
    try {
      const formatted = `+${rawDigits}`;
      const data = await api.register({ full_name: name.trim(), whatsapp: formatted });
      dispatch({ type: 'SET_MEMBER', id: data.member_id, name: name.trim() });
      navigate('/consent');
    } catch (err) {
      if (err.code === 'WHATSAPP_ALREADY_REGISTERED') {
        setError('Este WhatsApp já está cadastrado. Verifique o número e tente novamente.');
      } else {
        setError(err.message || 'Erro ao cadastrar. Tente novamente.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="screen" style={{ paddingTop: 40, gap: 24, justifyContent: 'center' }}>
      <div className="anim-fade-in-up" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 12 }}>
        <img src="/logo.jpg" alt="CCI Aliança" style={{ width: 56, height: 56, borderRadius: '50%', objectFit: 'cover' }} />
        <div>
          <h1 style={{ marginBottom: 8 }}>Cadastro</h1>
          <p>Preencha seus dados para continuar.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="anim-fade-in-up delay-1" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <label className="input-label" htmlFor="name">Nome completo</label>
          <input
            id="name"
            className="input"
            type="text"
            placeholder="Seu nome completo"
            autoComplete="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="input-label" htmlFor="whatsapp">WhatsApp</label>
          <input
            id="whatsapp"
            className="input"
            type="tel"
            placeholder="+55 (11) 99999-9999"
            inputMode="tel"
            autoComplete="tel"
            value={whatsapp}
            onChange={(e) => setWhatsapp(formatWhatsApp(e.target.value))}
            maxLength={19}
            required
          />
          <p style={{ fontSize: 12, marginTop: 6, color: 'var(--text-muted)' }}>
            Enviaremos um código de verificação para este número.
          </p>
        </div>

        {error && <div className="error-msg">{error}</div>}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={!valid || loading}
          style={{ marginTop: 8 }}
        >
          {loading ? <span className="spinner" /> : 'Continuar'}
        </button>
      </form>
    </div>
  );
}
